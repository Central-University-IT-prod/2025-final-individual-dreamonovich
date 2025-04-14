import uuid
import random
import time
import numpy as np

from django.core.management.base import BaseCommand
from client.models import Impression, Click

BATCH_SIZE = 1_000  # Insert in batches of 100K rows


class Command(BaseCommand):
    help = "Stress test ClickHouse by inserting 10 million impressions and clicks."

    def add_arguments(self, parser):
        parser.add_argument(
            "--total-impressions",
            type=int,
            default=10_000_000,
            help="Number of impressions to insert",
        )
        parser.add_argument(
            "--click-chance",
            dest="click_chance",
            type=float,
            default=0.3,
            help="Probability (0.0 to 1.0) that an impression generates a click",
        )

    def handle(self, *args, **options):
        total_impressions = options["total_impressions"]
        click_chance = options["click_chance"]

        self.stdout.write(
            self.style.WARNING(
                f"Inserting {total_impressions:,} impressions into ClickHouse..."
            )
        )

        start_time = time.time()

        # Generate bulk data
        num_batches = total_impressions // BATCH_SIZE
        total_clicks = 0

        for batch in range(num_batches):
            impressions_batch = []
            clicks_batch = []

            # Use NumPy for fast random number generation
            client_ids = [uuid.uuid4() for _ in range(BATCH_SIZE)]
            advertiser_ids = [uuid.uuid4() for _ in range(BATCH_SIZE)]
            ad_ids = [uuid.uuid4() for _ in range(BATCH_SIZE)]
            costs = np.random.randint(1, 100, size=BATCH_SIZE)  # Random costs
            days = np.random.randint(1, 100, size=BATCH_SIZE)  # Random campaign days

            # Create impressions
            for i in range(BATCH_SIZE):
                impressions_batch.append(
                    Impression(
                        client_id=client_ids[i],
                        cost=costs[i],
                        advertiser_id=advertiser_ids[i],
                        advertisement_id=ad_ids[i],
                        day=days[i],
                        month_block=abs((days[i] - 1) // 30),
                    )
                )

                # Generate a click based on probability
                if random.random() < click_chance:
                    click_day = random.randint(
                        days[i], days[i] + 30
                    )  # Clicks occur same day or later
                    click_cost = np.random.randint(10, 500)  # Random click cost
                    clicks_batch.append(
                        Click(
                            client_id=client_ids[i],
                            cost=click_cost,
                            advertiser_id=advertiser_ids[i],
                            advertisement_id=ad_ids[i],
                            day=click_day,
                            month_block=abs((click_day - 1) // 30),
                        )
                    )

            # Bulk insert into ClickHouse
            Impression.objects.bulk_create(impressions_batch, batch_size=BATCH_SIZE)
            Click.objects.bulk_create(clicks_batch, batch_size=BATCH_SIZE)

            total_clicks += len(clicks_batch)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Batch {batch + 1}/{num_batches}: Inserted {BATCH_SIZE:,} impressions, {len(clicks_batch):,} clicks"
                )
            )

        elapsed_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"Inserted {total_impressions:,} impressions and {total_clicks:,} clicks in {elapsed_time:.2f} seconds."
            )
        )
