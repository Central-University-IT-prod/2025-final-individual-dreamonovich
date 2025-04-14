import uuid
import random

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from faker import Faker

# Import your models
from business.models import Advertiser, Campaign
from client.models import Client, Impression, Click, Score


class Command(BaseCommand):
    help = (
        "Generates sample data for Advertiser, Campaign, Client (PostgreSQL) "
        "and Impression/Click (ClickHouse), including Score generation."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--advertisers", type=int, default=5, help="Number of advertisers to create"
        )
        parser.add_argument(
            "--campaigns", type=int, default=10, help="Number of campaigns to create"
        )
        parser.add_argument(
            "--clients", type=int, default=20, help="Number of clients to create"
        )
        parser.add_argument(
            "--impressions",
            type=int,
            default=100,
            help="Number of impressions to create",
        )
        parser.add_argument(
            "--click-chance",
            dest="click_chance",
            type=float,
            default=0.3,
            help="Probability (0.0 to 1.0) that an impression generates a click",
        )

    def handle(self, *args, **options):
        fake = Faker()

        num_advertisers = options["advertisers"]
        num_campaigns = options["campaigns"]
        num_clients = options["clients"]
        num_impressions = options["impressions"]
        click_chance = options["click_chance"]

        self.stdout.write("Generating Advertisers...")
        advertisers = []
        for _ in range(num_advertisers):
            advertiser = Advertiser(id=uuid.uuid4(), name=fake.company())
            advertiser.save()
            advertisers.append(advertiser)
        self.stdout.write(
            self.style.SUCCESS(f"Created {len(advertisers)} advertisers.")
        )

        self.stdout.write("Generating Campaigns...")
        campaigns = []
        for _ in range(num_campaigns):
            adv = random.choice(advertisers)
            start_day = random.randint(1, 10)
            end_day = random.randint(start_day, start_day + 5)
            age_from = random.randint(18, 40)
            age_to = random.randint(age_from + 1, 65)

            campaign = Campaign(
                impressions_limit=random.randint(1000, 10000),
                clicks_limit=random.randint(100, 1000),
                cost_per_impression=round(random.uniform(0.01, 1.00), 2),
                cost_per_click=round(random.uniform(0.1, 5.00), 2),
                ad_title=fake.sentence(nb_words=6),
                ad_text=fake.text(max_nb_chars=200),
                start_date=start_day,
                end_date=end_day,
                targeted_gender=random.choice(["MALE", "FEMALE", "ALL"]),
                targeted_age_from=age_from,
                targeted_age_to=age_to,
                erid=fake.bothify(text="???-########"),
                advertiser=adv,
            )
            campaign.save()
            campaigns.append(campaign)
        self.stdout.write(self.style.SUCCESS(f"Created {len(campaigns)} campaigns."))

        self.stdout.write("Generating Clients...")
        clients = []
        for _ in range(num_clients):
            client = Client(
                id=uuid.uuid4(),
                login=fake.user_name(),
                age=random.randint(18, 70),
                location=fake.city(),
                gender=random.choice(["MALE", "FEMALE"]),
            )
            client.save()
            clients.append(client)
        self.stdout.write(self.style.SUCCESS(f"Created {len(clients)} clients."))

        self.stdout.write("Generating Impressions and Clicks in ClickHouse...")
        impressions = []
        clicks = []
        for _ in range(num_impressions):
            while True:
                try:
                    client = random.choice(clients)
                    campaign = random.choice(campaigns)
                    advertiser = campaign.advertiser

                    impression_day = random.randint(campaign.start_date, campaign.end_date)
                    impression = Impression(
                        client_id=client.id,
                        cost=int(random.uniform(1, 100)),
                        advertiser_id=advertiser.id,
                        advertisement_id=campaign.id,
                        day=impression_day,
                    )
                    impression.save()
                    break
                except IntegrityError:
                    pass
            impressions.append(impression)

            if random.random() < click_chance:
                click_day = random.randint(impression_day, campaign.end_date)
                click_cost = int(campaign.cost_per_click * 100)
                click = Click(
                    client_id=client.id,
                    cost=click_cost,
                    advertiser_id=advertiser.id,
                    advertisement_id=campaign.id,
                    day=click_day,
                )
                click.save()
                clicks.append(click)

        self.stdout.write(
            self.style.SUCCESS(f"Created {len(impressions)} impressions.")
        )
        self.stdout.write(self.style.SUCCESS(f"Created {len(clicks)} clicks."))

        self.stdout.write("Generating Scores...")
        scores = []
        for client in clients:
            for advertiser in advertisers:
                score_value = random.randint(1, 100)  # Arbitrary score value
                score = Score(client=client, advertiser=advertiser, score=score_value)
                score.save()
                scores.append(score)

        self.stdout.write(self.style.SUCCESS(f"Created {len(scores)} scores."))
        self.stdout.write(self.style.SUCCESS("Data generation complete."))
