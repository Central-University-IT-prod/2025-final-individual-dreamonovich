import requests
import random
import time
from django.core.management.base import BaseCommand
from concurrent.futures import ThreadPoolExecutor
from client.models import Client  # Adjust to your actual Client model import


class Command(BaseCommand):
    help = "Stress test the /ads endpoint with random client_id from clients table and calculate average response time."

    def add_arguments(self, parser):
        parser.add_argument("url", type=str, help="The base URL of the API to test.")
        parser.add_argument(
            "--rps", type=int, default=500, help="Requests per second (default: 500)."
        )
        parser.add_argument(
            "--duration",
            type=int,
            default=10,
            help="Duration for the test in seconds (default: 10).",
        )

    def get_all_client_ids(self):
        # Fetch all client_ids from the clients table
        client_ids = list(Client.objects.values_list("id", flat=True))
        return client_ids

    def send_request(self, url, client_ids, response_times):
        try:
            # Get a random client_id from pre-fetched client_ids
            client_id = random.choice(client_ids)
            full_url = f"{url}?client_id={client_id}"

            start_time = time.time()  # Start measuring response time
            response = requests.get(full_url)
            end_time = time.time()  # End measuring response time

            # Calculate the response time and add it to the list
            response_time = end_time - start_time
            response_times.append(response_time)

            print(
                f"Sent request to {full_url}, Response: {response.status_code}, Time: {response_time:.4f}s"
            )
        except Exception as e:
            print(f"Error while sending request: {e}")

    def handle(self, *args, **kwargs):
        url = kwargs["url"]
        rps = kwargs["rps"]
        duration = kwargs["duration"]

        print(
            f"Starting stress test on {url} with {rps} requests per second for {duration} seconds."
        )

        # Fetch all client_ids before starting the test
        client_ids = self.get_all_client_ids()

        if not client_ids:
            print("No clients found in the database.")
            return

        response_times = []  # List to store response times

        # Use ThreadPoolExecutor to simulate the requests per second
        with ThreadPoolExecutor(max_workers=rps) as executor:
            start_time = time.time()
            end_time = start_time + duration

            while time.time() < end_time:
                # Dispatch a request every second to maintain steady load
                for _ in range(rps):
                    executor.submit(self.send_request, url, client_ids, response_times)

            # Calculate the average response time after the test
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                print(
                    f"\nStress test finished. Total time: {time.time() - start_time:.2f} seconds."
                )
                print(f"Total requests made: {len(response_times)}")
                print(f"Average response time: {avg_response_time:.4f} seconds.")
            else:
                print("No requests were made, so no response time data is available.")
