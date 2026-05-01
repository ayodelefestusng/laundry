"""
One-time management command to seed landing page defaults for ALL existing tenants
that don't already have landing content.

Usage:
    python manage.py seed_landing_defaults          # seed all tenants missing content
    python manage.py seed_landing_defaults --force   # re-seed even if content exists
"""
from django.core.management.base import BaseCommand
from myapp.models import Tenant
from myapp.landing_models import (
    LandingText, LandingValue, LandingCommitment,
    LandingPricingCard, LandingCustomerStory, LandingFAQ,
)


class Command(BaseCommand):
    help = "Seed landing page default content for existing tenants that are missing it."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-seed content even if the tenant already has landing data (deletes existing first).',
        )

    def handle(self, *args, **options):
        force = options['force']
        tenants = Tenant.objects.filter(is_active=True)
        seeded = 0
        skipped = 0

        for tenant in tenants:
            has_content = LandingText.objects.filter(tenant=tenant).exists()

            if has_content and not force:
                self.stdout.write(self.style.WARNING(f"  SKIP  {tenant.name} — already has landing content"))
                skipped += 1
                continue

            if has_content and force:
                # Wipe existing content before re-seeding
                for model in [LandingText, LandingValue, LandingCommitment,
                              LandingPricingCard, LandingCustomerStory, LandingFAQ]:
                    model.objects.filter(tenant=tenant).delete()
                self.stdout.write(self.style.WARNING(f"  RESET {tenant.name} — cleared existing content"))

            self._seed(tenant)
            seeded += 1
            self.stdout.write(self.style.SUCCESS(f"  DONE  {tenant.name} — defaults seeded"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Finished: {seeded} seeded, {skipped} skipped."))

    def _seed(self, tenant):
        """Identical logic to TenantGenericFormMixin._seed_landing_defaults"""

        # 1. Hero Text
        LandingText.objects.create(
            tenant=tenant,
            hero_title="Laundry Made Simple, Fresh & Fast.",
            hero_subtitle="Experience premium garment care with free doorstep pickup & delivery. "
                          "Eco-friendly cleaning that preserves your clothes and the planet.",
        )

        # 2. Value Propositions
        LandingValue.objects.bulk_create([
            LandingValue(tenant=tenant, value_text="Free Pickup & Delivery",
                         value_subtext="Right from your doorstep", icon_class="fas fa-truck-fast"),
            LandingValue(tenant=tenant, value_text="24h Turnaround",
                         value_subtext="Express services available", icon_class="fas fa-stopwatch"),
            LandingValue(tenant=tenant, value_text="Eco-Friendly Care",
                         value_subtext="Non-toxic, safe detergents", icon_class="fas fa-leaf"),
        ])

        # 3. About / Commitment
        LandingCommitment.objects.create(
            tenant=tenant,
            committed_to="Committed to Garment Care and Our Community",
            we_believe="We believe that doing laundry shouldn't cost the earth. "
                       "That's why we've pioneered a sustainable approach to garment care.",
            eco_friendly="Non-toxic Detergents: Safe for sensitive skin and the environment.",
        )

        # 4. Pricing Cards
        LandingPricingCard.objects.bulk_create([
            LandingPricingCard(
                tenant=tenant, title="Wash & Fold", is_popular=False,
                description="Perfect for everyday wear.", price=800,
                features=["Wash & Tumble Dry", "Neat Folding", "Eco-friendly Detergents"],
            ),
            LandingPricingCard(
                tenant=tenant, title="Wash & Iron", is_popular=True,
                description="Crisp, wrinkle-free garments.", price=1200,
                features=["Wash & Steam Iron", "Premium Hanger Pack", "Spot Treatment"],
            ),
            LandingPricingCard(
                tenant=tenant, title="Premium Dry Clean", is_popular=False,
                description="For delicate & special fabrics.", price=2500,
                features=["Chemical-free Solvents", "Hand Finishing", "Minor Alterations"],
            ),
        ])

        # 5. Customer Stories
        LandingCustomerStory.objects.bulk_create([
            LandingCustomerStory(
                tenant=tenant,
                story="I absolutely loved how fresh and neatly folded my clothes arrived. "
                      "There was no harsh smell, no wrinkles, and the fabric felt softer than before.",
                name="Happy Customer", stars=5, is_verified=True,
            ),
            LandingCustomerStory(
                tenant=tenant,
                story="I trusted them with my delicate gowns and formal outfits, and they returned "
                      "looking brand-new. Truly world-class.",
                name="Satisfied Client", stars=5, is_verified=True,
            ),
            LandingCustomerStory(
                tenant=tenant,
                story="The curtains and sofa covers I sent were returned spotless, neatly packed, "
                      "and smelling wonderfully fresh. Highly recommend!",
                name="Loyal Customer", stars=5, is_verified=True,
            ),
        ])

        # 6. FAQs
        LandingFAQ.objects.bulk_create([
            LandingFAQ(
                tenant=tenant,
                question="What is your turnaround time?",
                answer="Standard delivery takes 48-72 hours. We also offer Express Delivery "
                       "for a 24-hour turnaround at a minimal extra charge.",
            ),
            LandingFAQ(
                tenant=tenant,
                question="What if I'm not home for pickup or delivery?",
                answer="You can leave your laundry bag with your concierge, security desk, or a "
                       'designated safe spot. Just let us know in the "Special Instructions" when booking.',
            ),
            LandingFAQ(
                tenant=tenant,
                question="Do you mix my clothes with others?",
                answer="Absolutely not. We process every customer's order individually in dedicated "
                       "machines to maintain strict hygiene standards.",
            ),
        ])
