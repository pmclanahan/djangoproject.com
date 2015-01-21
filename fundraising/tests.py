import requests_mock

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from .models import DjangoHero


class TestIndex(TestCase):

    @classmethod
    @requests_mock.mock()
    def setUpClass(cls, mocker):
        mocker.register_uri(
            'GET',
            'https://api.stripe.com/v1/customers',
            status_code=200
        )

    def test_donors_count(self):
        DjangoHero.objects.create()
        response = self.client.get('/fundraising/')
        self.assertEqual(response.context['total_donors'], 1)

    def test_render_donate_form_with_amount(self):
        response = self.client.get(reverse('fundraising:donate'), {'amount': 50})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['fixed_amount'], '50')
        self.assertEqual(response.context['publishable_key'], settings.STRIPE_PUBLISHABLE_KEY)

        # Checking if amount field is hidden
        self.assertEqual(response.context['form'].fields['amount'].widget.__class__, forms.HiddenInput)
        # Checking if campaign field is empty
        self.assertEqual(response.context['form'].initial['campaign'], None)

    def test_render_donate_form_without_amount(self):
        response = self.client.get(reverse('fundraising:donate'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['fixed_amount'], None)
        self.assertEqual(response.context['publishable_key'], settings.STRIPE_PUBLISHABLE_KEY)

        # Checking if amount field is visible
        self.assertEqual(response.context['form'].fields['amount'].widget.__class__, forms.TextInput)
        # Checking if campaign field is empty
        self.assertEqual(response.context['form'].initial['campaign'], None)

    def test_render_donate_form_with_campaign(self):
        campaign = 'sample'
        response = self.client.get(reverse('fundraising:donate'), {'amount': 100, 'campaign':campaign})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['fixed_amount'], '100')
        self.assertEqual(response.context['publishable_key'], settings.STRIPE_PUBLISHABLE_KEY)

        # Checking if amount field is hidden
        self.assertEqual(response.context['form'].fields['amount'].widget.__class__, forms.HiddenInput)
        # Checking if campaign field is same as campaign
        self.assertEqual(response.context['form'].initial['campaign'], campaign)

    def test_submitting_donation_form(self):
        response = self.client.post(reverse('fundraising:donate'), {'amount': 100})
        self.assertFalse(response.context['form'].is_valid())

        response = self.client.post(reverse('fundraising:donate'), {
            'amount': 100,
            'number': '4242424242424242',
            'cvc': '111',
            'expires': '11/18',
            'campaign': None,
            'stripe_token': 'test',
        })
        self.assertTrue(response.context['form'].is_valid())
