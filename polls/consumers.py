import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Poll, Choice
import asyncio

class PollConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.poll_id = self.scope['url_route']['kwargs']['poll_id']
        self.poll_group_name = f'poll_{self.poll_id}'

        # Join poll group
        await self.channel_layer.group_add(
            self.poll_group_name,
            self.channel_name
        )

        try:
            await self.accept()
            # Send initial poll data
            initial_data = await self.get_poll_data()
            if initial_data:
                await self.send(text_data=json.dumps(initial_data))
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.close()

    @database_sync_to_async
    def get_poll_data(self):
        try:
            poll = Poll.objects.get(id=self.poll_id)
            choices_data = []
            total_votes = poll.get_vote_count
            for choice in poll.choice_set.all():
                choice_votes = choice.get_vote_count
                choices_data.append({
                    'id': choice.id,
                    'votes': choice_votes,
                    'percentage': round((choice_votes / total_votes * 100), 1) if total_votes > 0 else 0
                })
            return {'choices': choices_data}
        except Poll.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error getting poll data: {e}")
            return None

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.poll_group_name,
                self.channel_name
            )
        except Exception as e:
            print(f"Error in disconnect: {e}")

    async def poll_update(self, event):
        try:
            await self.send(text_data=json.dumps(event['data']))
        except Exception as e:
            print(f"Error in poll_update: {e}") 