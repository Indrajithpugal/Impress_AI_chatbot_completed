import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .reply_factory import generate_bot_responses


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        try:
            self.group_name = self.scope["session"].session_key

            if not self.group_name:
                print("Session key missing! Closing connection.")
                self.close()
                return

            # Initialize session variables
            if "current_question_id" not in self.scope["session"]:
                self.scope["session"]["current_question_id"] = 0
            if "message_history" not in self.scope["session"]:
                self.scope["session"]["message_history"] = []

            # Save the session
            self.scope["session"].save()

            print(f"WebSocket connected: {self.group_name} ({self.scope['client']})")
            async_to_sync(self.channel_layer.group_add)(
                self.group_name, self.channel_name
            )
            self.accept()
        except Exception as e:
            print(f"Error during WebSocket connection: {e}")
            self.close()

    def disconnect(self, close_code):
        try:
            print(f"WebSocket disconnected: {self.group_name} with code {close_code}")
            async_to_sync(self.channel_layer.group_discard)(
                self.group_name, self.channel_name
            )
        except Exception as e:
            print(f"Error during WebSocket disconnection: {e}")

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            user_message = text_data_json.get("message", "").strip()

            if not user_message:
                self.send_message(
                    "Answer cannot be empty or just whitespace.", is_user=False
                )
                return

            print(f"Message received: {user_message}")

            # Handle reset command
            if user_message == "/reset":
                self.reset_session()
                self.send_message(
                    "Session reset. You can start the quiz again.", is_user=False
                )
                return

            # Save user message and send to WebSocket
            self.send_message(user_message, is_user=True)

            # Generate bot responses
            bot_responses = generate_bot_responses(user_message, self.scope["session"])

            for bot_response in bot_responses:
                self.send_message(bot_response, is_user=False)

            # Debugging session after processing
            print(f"Session after processing: {self.scope['session']}")

        except Exception as e:
            print(f"Error during WebSocket message handling: {e}")
            self.close()

    def send_message(self, text, is_user):
        try:
            message_obj = {
                "type": "chat_message",
                "is_user": is_user,
                "text": text,
            }
            async_to_sync(self.channel_layer.group_send)(self.group_name, message_obj)
        except Exception as e:
            print(f"Error sending message to WebSocket: {e}")

    def chat_message(self, message_obj):
        try:
            print(f"Sending message to WebSocket: {message_obj}")
            self.send(text_data=json.dumps(message_obj))
            self.add_to_history(message_obj)
        except Exception as e:
            print(f"Error sending message to WebSocket: {e}")

    def reset_session(self):
        try:
            self.scope["session"]["current_question_id"] = 0
            self.scope["session"]["message_history"] = []
            self.scope["session"].save()
            print("Session reset successfully.")
        except Exception as e:
            print(f"Error resetting session: {e}")

    def add_to_history(self, message_obj):
        try:
            message_history = self.scope["session"].get("message_history", [])
            message_history.append(message_obj)
            self.scope["session"]["message_history"] = message_history
            self.scope["session"].save()
        except Exception as e:
            print(f"Error updating message history: {e}")
