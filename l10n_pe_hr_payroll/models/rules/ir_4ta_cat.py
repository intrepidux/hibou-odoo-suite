# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

def ir_4ta_cat(payslip, categories, worked_days, inputs):
    if payslip.contract_id.pe_payroll_ee_4ta_cat_exempt:
        return 0.0, 0.0
    wage = categories.GROSS
    rate = payslip.rule_parameter('ee_ir_4ta_cat')
    return wage, -rate
