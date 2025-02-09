# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models

ACCOUNT_PAYABLE = '211000'
SALARY_EXPENSES = '630000'


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    def _load(self, sale_tax_rate, purchase_tax_rate, company):
        """
        Override to configure payroll accounting data as well as accounting data.
        """
        res = super()._load(sale_tax_rate, purchase_tax_rate, company)
        self._us_configure_payroll_account_data(company)
        return res

    def _us_configure_payroll_account_data(self, companies, ap_code=ACCOUNT_PAYABLE, salary_exp_code=SALARY_EXPENSES,
                                           salary_rules=None, full_reset=False):
        account_codes = (
            ap_code,
            salary_exp_code,
        )
        us_structures = self.env['hr.payroll.structure'].search([('country_id', '=', self.env.ref('base.us').id)])
        journal_field_id = self.env['ir.model.fields'].search([
            ('model', '=', 'hr.payroll.structure'),
            ('name', '=', 'journal_id')], limit=1)

        for company in companies:
            self = self.with_context({'allowed_company_ids': company.ids})
            accounts = {
                code: self.env['account.account'].search(
                    [('company_id', '=', company.id), ('code', '=like', '%s%%' % code)], limit=1)
                for code in account_codes
            }
            accounts['none'] = self.env['account.account'].browse()

            def set_rule_accounts(code, account_debit, account_credit):
                rule_domain = [
                    ('struct_id', 'in', us_structures.ids),
                    ('code', '=like', code),
                ]
                if salary_rules:
                    rule_domain.append(('id', 'in', salary_rules.ids))
                rules = self.env['hr.salary.rule'].search(rule_domain)
                if full_reset:
                    values = {
                        'account_debit': account_debit.id,
                        'account_credit': account_credit.id,
                    }
                    rules.write(values)
                else:
                    # we need to ensure we do not update an account that is already set
                    for rule in rules:
                        values = {}
                        if account_debit and not rule.account_debit:
                            values['account_debit'] = account_debit.id
                        if account_credit and not rule.account_credit:
                            values['account_credit'] = account_credit.id
                        if values:
                            # save a write if no values to write
                            rule.write(values)

            journal = self.env['account.journal'].search([
                ('code', '=', 'PAYR'),
                ('name', '=', 'Payroll'),
                ('company_id', '=', company.id),
            ])
            if journal:
                if not journal.default_account_id:
                    journal.default_account_id = accounts[salary_exp_code].id
                if hasattr(journal, 'payroll_entry_type'):
                    journal.payroll_entry_type = 'grouped'
            else:
                journal = self.env['account.journal'].create({
                    'name': 'Payroll',
                    'code': 'PAYR',
                    'type': 'general',
                    'company_id': company.id,
                    'default_account_id': accounts[salary_exp_code].id,
                })
                if hasattr(journal, 'payroll_entry_type'):
                    journal.payroll_entry_type = 'grouped'

                self.env['ir.property']._set_multi(
                    "journal_id",
                    "hr.payroll.structure",
                    {structure.id: journal for structure in us_structures},
                )

            # Find rules and set accounts on them.
            # Find all rules that are ...

            # BASIC* -> SALARY_EXPENSE debit account
            set_rule_accounts('BASIC%', accounts[salary_exp_code], accounts['none'])
            # ALW* -> SALARY_EXPENSE debit account
            set_rule_accounts('ALW%', accounts[salary_exp_code], accounts['none'])
            # EE_* -> AP debit
            set_rule_accounts('EE_%', accounts[ap_code], accounts['none'])
            # ER_* -> AP debit, SE credit
            set_rule_accounts('ER_%', accounts[ap_code], accounts[salary_exp_code])
            # NET* -> AP credit
            set_rule_accounts('NET%', accounts['none'], accounts[ap_code])
