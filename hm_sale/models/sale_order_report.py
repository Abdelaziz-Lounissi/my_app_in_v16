# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from io import BytesIO
import base64
import xlsxwriter
import dateutil.relativedelta


class SaleOrderReport(models.Model):
    _name = "sale.order.report"
    _description = "Sale Order Report"

    name = fields.Char('Name', default="Marges Report")
    date_intervention = fields.Datetime('Intervention Date')
    current_date = fields.Datetime('Current Date', default=datetime.now())

    @api.onchange('current_date')
    def get_date_from_to(self):
        for rec in self:
            rec.date_intervention = rec.current_date - dateutil.relativedelta.relativedelta(months=3)

    def validate(self):
        file_name = _('Marges report.xlsx')
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        heading_format = workbook.add_format({'align': 'center',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 12})
        heading_format.set_border()
        title_format = workbook.add_format({'align': 'center',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 14,'color':"00FF0000"})
        title_format.set_border()
        title_format.set_bg_color("6bcfc1")
        title_format.set_color("1f1626")
        cell_text_format_date = workbook.add_format({'align': 'center',
                                                  'bold': True, 'size': 9,
                                                  })
        cell_text_format_date.set_border()
        cell_text_format = workbook.add_format({'align': 'left',
                                                'bold': True, 'size': 9,
                                                })
        cell_text_format.set_border()
        cell_number_format = workbook.add_format({'align': 'right',
                                                  'bold': False, 'size': 9,
                                                  'num_format': '#,###0.00'})
        cell_number_format.set_border()
        worksheet = workbook.add_worksheet('Marge report')
        width = len("long text hidden test-1")
        normal_num_bold = workbook.add_format({'bold': True, 'num_format': '#,###0.00', 'size': 12 })
        normal_num_bold.set_border()
        worksheet.merge_range('C2:E2', 'Details SO', title_format)
        title = ['No SO', 'Date d’intervention', 'Client', 'Initial Margin Forecast',
                 'Preview Margin','Total purchase invoice','Total purchase refund','Total sale invoice',
                 'Total sale refund','Total Marges','Vendeur','SO Manager','Catégorie de devis']
        row = 0
        col = 0
        fin_sheet = 3
        j = 0
        for j, t in enumerate(title):
            worksheet.write(4, col + j, t, heading_format)
            worksheet.set_column(4, col + j, width)
            j += 1
        fin_sheet += j
        SO_ids = self.env['sale.order'].search(
            [('commitment_date', '>=', self.date_intervention), ('commitment_date', '<=', self.current_date), ('state', '=', 'sale')])
        rw = 5
        cl = 0
        k=0
        if SO_ids:
            for so_id in SO_ids:
                total_marges = 0.0
                total_invoices_purchase = 0
                total_refund_purchase = 0
                invoices_purchase = so_id.mapped('purchase_ids.invoice_ids').filtered(lambda x: x.state == "posted" and x.move_type == "in_invoice")
                total_invoices_purchase = sum([x.amount_untaxed for x in invoices_purchase])
                refund_purchase = so_id.mapped('purchase_ids.invoice_ids').filtered(lambda x: x.state == "posted" and x.move_type == "in_refund")
                total_refund_purchase = sum([x.amount_untaxed for x in refund_purchase])

                total_invoices_sale = 0
                total_refund_sale = 0
                invoices_sale = so_id.mapped('invoice_ids').filtered(
                    lambda x: x.state == "posted" and x.move_type == "out_invoice")
                total_invoices_sale = sum([x.amount_untaxed for x in invoices_sale])
                refund_sale = so_id.mapped('invoice_ids').filtered(
                    lambda x: x.state == "posted" and x.type == "out_refund")
                total_refund_sale = sum([x.amount_untaxed for x in refund_sale])
                total_marges = total_invoices_sale - total_refund_sale - total_invoices_purchase + total_refund_purchase

                worksheet.write(rw+k, cl , so_id.name, cell_text_format)
                worksheet.write(rw + k, 1, str(so_id.commitment_date.date()), cell_text_format_date)
                worksheet.write(rw + k, 2, so_id.partner_id.name, cell_text_format)
                worksheet.write(rw + k, 3, so_id.hm_initial_margin_forecast, cell_number_format)
                # worksheet.write(rw + k, 4, so_id.hm_preview_margin, cell_number_format)
                worksheet.write(rw + k, 5, total_invoices_purchase, cell_number_format)
                worksheet.write(rw + k, 6, total_refund_purchase, cell_number_format)
                worksheet.write(rw + k, 7, total_invoices_sale, cell_number_format)
                worksheet.write(rw + k, 8, total_refund_sale, cell_number_format)
                worksheet.write(rw + k, 9, total_marges, cell_number_format)
                worksheet.write(rw + k, 10, so_id.user_id.name, cell_text_format)
                worksheet.write(rw + k, 11, so_id.hm_so_manager_id.name, cell_text_format)
                worksheet.write(rw + k, 12, so_id.sale_order_template_id.hm_work_category.hm_works_category_parent_id.name, cell_text_format)
                k += 1
            fin_sheet += k
        workbook.close()
        file_download = base64.b64encode(fp.getvalue())
        fp.close()
        attach_id = self.env['report.excel'].create({
            'name': file_name,
            'file_download': file_download,
        })
        return {
            'name': file_name,
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.excel&id=" + str(
                attach_id.id) + "&filename_field=file_name&field=file_download&download=true&filename=" + file_name,
            'target': 'new'
        }


class ReportExcel(models.TransientModel):
    _name = 'report.excel'
    _description = 'Excel'

    name = fields.Char('File Name', size=256, readonly=True)
    file_download = fields.Binary('Download report', readonly=True)



