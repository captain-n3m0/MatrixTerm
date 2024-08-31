import argparse
import asyncio
import sys
import os
from nio import AsyncClient, LoginResponse, RoomMessageText, RoomMessageMedia, RoomMemberEvent, RoomCreateEvent
from aiofile import AIOFile

class MatrixCLI:
    def __init__(self, homeserver, config_file=None):
        self.client = AsyncClient(homeserver)
        self.client.add_event_callback(self.handle_events, (RoomMessageText, RoomMessageMedia, RoomMemberEvent, RoomCreateEvent))
        self.rooms = {}
        self.config_file = config_file

    async def login(self, username, password):
        response = await self.client.login(username=username, password=password)
        if isinstance(response, LoginResponse):
            print("Logged in successfully.")
            if self.config_file:
                await self.save_config(username, password)
        else:
            print("Login failed.")
            sys.exit(1)

    async def start(self):
        await self.client.sync_forever(timeout=30000, full_state=True)

    async def handle_events(self, event):
        if isinstance(event, RoomMessageText):
            print(f"{event.sender}: {event.body}")
        elif isinstance(event, RoomMessageMedia):
            print(f"{event.sender} sent media: {event.body.get('url')}")
        elif isinstance(event, RoomMemberEvent):
            if event.membership == "join":
                print(f"{event.sender} joined the room.")
        elif isinstance(event, RoomCreateEvent):
            self.rooms[event.room_id] = event.content.get("room_name", "Unnamed Room")

    async def send_message(self, room_id, message):
        try:
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message
                }
            )
            print("Message sent.")
        except Exception as e:
            print(f"Failed to send message: {e}")

    async def join_room(self, room_id):
        try:
            await self.client.join(room_id)
            print(f"Joined room {room_id}.")
            self.rooms[room_id] = "Unnamed Room"
        except Exception as e:
            print(f"Failed to join room: {e}")

    def list_rooms(self):
        print("Rooms:")
        for room_id, room_name in self.rooms.items():
            print(f"{room_id}: {room_name}")

    async def close(self):
        await self.client.close()

    async def leave_room(self, room_id):
        try:
            await self.client.room_leave(room_id)
            print(f"Left room {room_id}.")
            if room_id in self.rooms:
                del self.rooms[room_id]
        except Exception as e:
            print(f"Failed to leave room: {e}")

    async def direct_message(self, user_id, message):
        try:
            room_id = await self.client.room_create(is_direct=True, invitees=[user_id])
            await self.send_message(room_id, message)
            print(f"Sent direct message to {user_id}.")
        except Exception as e:
            print(f"Failed to send direct message: {e}")

    async def get_message_history(self, room_id, limit=10):
        try:
            messages = await self.client.room_get_messages(room_id, limit=limit)
            print(f"Message history for room {room_id}:")
            for message in messages['chunk']:
                sender = message['sender']
                content = message['content']['body']
                print(f"{sender}: {content}")
        except Exception as e:
            print(f"Failed to retrieve message history: {e}")

    async def save_config(self, username, password):
        config_data = f"[login]\nusername={username}\npassword={password}\n"
        async with AIOFile(self.config_file, 'w') as afp:
            await afp.write(config_data)

    @staticmethod
    def load_config(config_file):
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                lines = f.readlines()
                config = {}
                for line in lines:
                    if '=' in line:
                        key, value = line.strip().split('=')
                        config[key] = value
                return config.get('username'), config.get('password')
        return None, None

async def main():
    parser = argparse.ArgumentParser(description="Matrix CLI Client")

    usage = r"""
ooo        ooooo               .             o8o                   ooooooooooooo
`88.       .888'             .o8             `"'                   8'   888   `8
 888b     d'888   .oooo.   .o888oo oooo d8b oooo  oooo    ooo           888       .ooooo.  oooo d8b ooo. .oo.  .oo.
 8 Y88. .P  888  `P  )88b    888   `888""8P `888   `88b..8P'            888      d88' `88b `888""8P `888P"Y88bP"Y88b
 8  `888'   888   .oP"888    888    888      888     Y888'              888      888ooo888  888      888   888   888
 8    Y     888  d8(  888    888 .  888      888   .o8"'88b             888      888    .o  888      888   888   888
o8o        o888o `Y888""8o   "888" d888b    o888o o88'   888o          o888o     `Y8bod8P' d888b    o888o o888o o888o

Welcome to MatrixTerm! Developed by captain-n3m0."""

    parser.usage = usage

    parser.add_argument("--homeserver", required=True, help="Matrix homeserver URL")
    parser.add_argument("--username", help="Matrix username")
    parser.add_argument("--password", help="Matrix password")
    parser.add_argument("--config", help="Configuration file path", default="matrix_config.ini")
    args = parser.parse_args()

    username, password = args.username, args.password
    if not username or not password:
        username, password = MatrixCLI.load_config(args.config)

    if not username or not password:
        print("Username and password are required.")
        sys.exit(1)

    matrix_cli = MatrixCLI(args.homeserver, config_file=args.config)
    await matrix_cli.login(username, password)

    asyncio.create_task(matrix_cli.start())

    print(usage)

    while True:
        print("\nOptions:")
        print("1. List rooms")
        print("2. Join room")
        print("3. Send message")
        print("4. Leave room")
        print("5. Send direct message")
        print("6. Get message history")
        print("7. Exit")
        choice = input("Select an option: ")

        if choice == "1":
            matrix_cli.list_rooms()
        elif choice == "2":
            room_id = input("Enter room ID to join: ")
            await matrix_cli.join_room(room_id)
        elif choice == "3":
            room_id = input("Enter room ID to send message: ")
            message = input("Enter message: ")
            await matrix_cli.send_message(room_id, message)
        elif choice == "4":
            room_id = input("Enter room ID to leave: ")
            await matrix_cli.leave_room(room_id)
        elif choice == "5":
            user_id = input("Enter user ID to send direct message: ")
            message = input("Enter message: ")
            await matrix_cli.direct_message(user_id, message)
        elif choice == "6":
            room_id = input("Enter room ID to get message history: ")
            await matrix_cli.get_message_history(room_id)
        elif choice == "7":
            await matrix_cli.close()
            break
        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
