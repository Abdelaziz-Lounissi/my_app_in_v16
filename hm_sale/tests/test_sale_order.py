import logging

from odoo.tests import common
import datetime as dt
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TestSaleOrder(common.TransactionCase):
    def setUp(self):
        super(TestSaleOrder, self).setUp()

    def test_update_po_deadline(self):
        # create new partner
        partner_id = self.env['res.partner'].create({
            'name': 'Partner TEST',
            'company_type': 'company',
        })
        technician_id = self.env['res.partner'].create({
            'name': 'Technician Test',
            'company_type': 'company',
        })
        # create new purchase
        purchase = self.env['purchase.order'].create({
            'partner_id': partner_id.id,
        })

        # create new primes
        hm_primes = self.env['hm.primes'].create({
            "name": "BXL 2022 - Boiler Thermodynamique TEST"
        })

        # create new primes line
        hm_premium = self.env['hm.so.primes.line'].create({
            'hm_prime_id': hm_primes.id,
            'hm_subtotal_prime': 100,

        })

        # ------------------------------------
        case_1A_date_now = dt.datetime.strptime('2022-08-22 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_1A_commitment_date = dt.datetime.strptime('2022-08-23 12:00:00', '%Y-%m-%d %H:%M:%S')
        case_1A_result = dt.datetime.strptime('2022-08-22 14:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_1A_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_1A_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_1A_result)

        case_1B_date_now = dt.datetime.strptime('2022-08-22 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_1B_commitment_date = dt.datetime.strptime('2022-08-24 09:30:00', '%Y-%m-%d %H:%M:%S')
        case_1B_result = dt.datetime.strptime('2022-08-22 14:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_1B_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_1B_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_1B_result)

        case_2A_date_now = dt.datetime.strptime('2022-08-22 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_2A_commitment_date = dt.datetime.strptime('2022-08-24 13:30:00', '%Y-%m-%d %H:%M:%S')
        case_2A_result = dt.datetime.strptime('2022-08-22 14:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_2A_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_2A_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_2A_result)

        case_2B_date_now = dt.datetime.strptime('2022-08-22 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_2B_commitment_date = dt.datetime.strptime('2022-08-24 14:30:00', '%Y-%m-%d %H:%M:%S')
        case_2B_result = dt.datetime.strptime('2022-08-22 14:30:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_2B_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_2B_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_2B_result)

        case_2C_date_now = dt.datetime.strptime('2022-08-22 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_2C_commitment_date = dt.datetime.strptime('2022-08-26 09:30:00', '%Y-%m-%d %H:%M:%S')
        case_2C_result = dt.datetime.strptime('2022-08-24 09:30:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_2C_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_2C_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_2C_result)

        case_3A_date_now = dt.datetime.strptime('2022-08-22 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_3A_commitment_date = dt.datetime.strptime('2022-08-26 10:30:00', '%Y-%m-%d %H:%M:%S')
        case_3A_result = dt.datetime.strptime('2022-08-24 10:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_3A_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_3A_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_3A_result)

        case_1A_weekend_date_now = dt.datetime.strptime('2022-09-23 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_1A_weekend_commitment_date = dt.datetime.strptime('2022-09-26 12:00:00', '%Y-%m-%d %H:%M:%S')
        case_1A_weekend_result = dt.datetime.strptime('2022-09-23 14:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_1A_weekend_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_1A_weekend_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_1A_weekend_result)

        case_1B_weekend_date_now = dt.datetime.strptime('2022-09-23 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_1B_weekend_commitment_date = dt.datetime.strptime('2022-09-27 08:00:00', '%Y-%m-%d %H:%M:%S')
        case_1B_weekend_result = dt.datetime.strptime('2022-09-23 14:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_1B_weekend_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_1B_weekend_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_1B_weekend_result)

        case_2A_weekend_date_now = dt.datetime.strptime('2022-09-23 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_2A_weekend_commitment_date = dt.datetime.strptime('2022-09-27 13:30:00', '%Y-%m-%d %H:%M:%S')
        case_2A_weekend_result = dt.datetime.strptime('2022-09-23 14:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_2A_weekend_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_2A_weekend_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_2A_weekend_result)

        case_2B_weekend_date_now = dt.datetime.strptime('2022-09-23 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_2B_weekend_commitment_date = dt.datetime.strptime('2022-09-27 14:30:00', '%Y-%m-%d %H:%M:%S')
        case_2B_weekend_result = dt.datetime.strptime('2022-09-23 14:30:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_2B_weekend_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_2B_weekend_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_2B_weekend_result)

        case_2C_weekend_date_now = dt.datetime.strptime('2022-09-23 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_2C_weekend_commitment_date = dt.datetime.strptime('2022-09-29 09:30:00', '%Y-%m-%d %H:%M:%S')
        case_2C_weekend_result = dt.datetime.strptime('2022-09-27 09:30:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_2C_weekend_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_2C_weekend_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_2C_weekend_result)

        case_3A_weekend_date_now = dt.datetime.strptime('2022-09-23 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_3A_weekend_commitment_date = dt.datetime.strptime('2022-09-29 10:30:00', '%Y-%m-%d %H:%M:%S')
        case_3A_weekend_result = dt.datetime.strptime('2022-09-27 10:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_3A_weekend_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_3A_weekend_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_3A_weekend_result)

        case_1A_national_holiday_date_now = dt.datetime.strptime('2022-10-31 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_1A_national_holiday_commitment_date = dt.datetime.strptime('2022-11-02 12:00:00', '%Y-%m-%d %H:%M:%S')
        case_1A_national_holiday_result = dt.datetime.strptime('2022-10-31 14:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_1A_national_holiday_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_1A_national_holiday_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_1A_national_holiday_result)

        case_1B_national_holiday_date_now = dt.datetime.strptime('2022-10-31 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_1B_national_holiday_commitment_date = dt.datetime.strptime('2022-11-03 09:30:00', '%Y-%m-%d %H:%M:%S')
        case_1B_national_holiday_result = dt.datetime.strptime('2022-10-31 14:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_1B_national_holiday_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_1B_national_holiday_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_1B_national_holiday_result)

        case_2A_national_holiday_date_now = dt.datetime.strptime('2022-10-31 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_2A_national_holiday_commitment_date = dt.datetime.strptime('2022-11-03 13:30:00', '%Y-%m-%d %H:%M:%S')
        case_2A_national_holiday_result = dt.datetime.strptime('2022-10-31 14:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_2A_national_holiday_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_2A_national_holiday_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_2A_national_holiday_result)

        case_2B_national_holiday_date_now = dt.datetime.strptime('2022-10-31 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_2B_national_holiday_commitment_date = dt.datetime.strptime('2022-11-03 14:30:00', '%Y-%m-%d %H:%M:%S')
        case_2B_national_holiday_result = dt.datetime.strptime('2022-10-31 14:30:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_2B_national_holiday_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_2B_national_holiday_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_2B_national_holiday_result)

        case_2C_national_holiday_date_now = dt.datetime.strptime('2022-10-31 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_2C_national_holiday_commitment_date = dt.datetime.strptime('2022-11-07 09:30:00', '%Y-%m-%d %H:%M:%S')
        case_2C_national_holiday_result = dt.datetime.strptime('2022-11-03 09:30:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_2C_national_holiday_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_2C_national_holiday_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_2C_national_holiday_result)

        case_3A_national_holiday_date_now = dt.datetime.strptime('2022-10-31 10:00:00', '%Y-%m-%d %H:%M:%S')
        case_3A_national_holiday_commitment_date = dt.datetime.strptime('2022-11-07 10:30:00', '%Y-%m-%d %H:%M:%S')
        case_3A_national_holiday_result = dt.datetime.strptime('2022-11-03 10:00:00', '%Y-%m-%d %H:%M:%S')
        sale = self.env['sale.order'].create({
            'partner_id': partner_id.id, 'state2': "planned",
            'commitment_date': case_3A_national_holiday_commitment_date,
            'hm_sum_premium_total': 0.0,
            'hm_amount_total_line_premium': 0.0,
            'hm_imputed_technician_id': technician_id.id,
            'purchase_ids': [(6, 0, purchase.id)],
            'hm_premium_ids': [(6, 0, hm_premium.id)], })
        sale.update_po_deadline(date_now=case_3A_national_holiday_date_now)
        self.assertEqual(purchase.hm_date_state2_update_deadline, case_3A_national_holiday_result)
