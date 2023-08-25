import argparse
import asyncio
import sys
from nio import AsyncClient, LoginResponse, RoomMessageText, RoomMessageMedia, RoomMemberEvent, RoomCreateEvent

class MatrixCLI:
    def __init__(self, homeserver):
        self.client = AsyncClient(homeserver)
        self.client.add_event_callback(self.handle_events, (RoomMessageText, RoomMessageMedia, RoomMemberEvent, RoomCreateEvent))
        self.rooms = {}

    async def login(self, username, password):
        response = await self.client.login(username=username, password=password)
        if isinstance(response, LoginResponse):
            print("Logged in successfully.")
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
        await self.client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": message
            }
        )
        print("Message sent.")

    async def join_room(self, room_id):
        await self.client.join(room_id)
        print(f"Joined room {room_id}.")
        self.rooms[room_id] = "Unnamed Room"

    def list_rooms(self):
        print("Rooms:")
        for room_id, room_name in self.rooms.items():
            print(f"{room_id}: {room_name}")

    async def close(self):
        await self.client.close()

async def main():
    parser = argparse.ArgumentParser(description="Matrix CLI Client")

    # Customize the usage message to include the ASCII art
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
    parser.add_argument("--username", required=True, help="Matrix username")
    parser.add_argument("--password", required=True, help="Matrix password")
    args = parser.parse_args()

    matrix_cli = MatrixCLI(args.homeserver)
    await matrix_cli.login(args.username, args.password)

    asyncio.create_task(matrix_cli.start())

    print(usage)

    while True:
        print("\nOptions:")
        print("1. List rooms")
        print("2. Join room")
        print("3. Send message")
        print("4. Exit")
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
            await matrix_cli.close()
            break
        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
