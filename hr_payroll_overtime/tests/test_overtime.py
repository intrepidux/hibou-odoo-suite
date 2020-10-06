from odoo.tests import common
from odoo.exceptions import UserError


class TestOvertime(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.overtime_rules = self.env['hr.work.entry.overtime.type'].create({
            'name': 'Test',
            'hours_per_week': 40.0,
            'multiplier': 1.5,
        })
        self.work_type_overtime = self.env['hr.work.entry.type'].create({
            'name': 'Test Overtime',
            'code': 'TEST_OT'
        })
        self.work_type = self.env['hr.work.entry.type'].create({
            'name': 'Test',
            'code': 'TEST',
            'overtime_type_id': self.overtime_rules.id,
            'overtime_work_type_id': self.work_type_overtime.id,
        })
        self.employee = self.env.ref('hr.employee_hne')
        self.payslip = self.env['hr.payslip'].create({
            'name': 'test slip',
            'employee_id': self.employee.id,
            'date_from': '2020-06-11',
            'date_to': '2020-06-15',
        })

    def test_02_overtime_aggregation(self):
        # 38 hours in 1 week
        work_data = [
            ((2020, 24, 1), [
                (self.work_type, 4.0, None),
                (self.work_type, 4.0, None),
            ]),
            ((2020, 24, 2), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
            ((2020, 24, 3), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
            ((2020, 24, 4), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
        ]
        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertTrue(self.work_type_overtime not in result_data)
        self.assertEqual(result_data[self.work_type][0], 4)
        self.assertEqual(result_data[self.work_type][1], 38.0)

        # 48 hours in 1 week
        work_data += [
            ((2020, 24, 5), [
                (self.work_type, 10.0, None),
            ]),
        ]
        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertEqual(result_data[self.work_type][0], 5)
        self.assertEqual(result_data[self.work_type][1], 40.0)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type_overtime][0], 0)
        self.assertEqual(result_data[self.work_type_overtime][1], 8.0)

        # 52 hours in 1 week
        work_data += [
            ((2020, 24, 6), [
                (self.work_type, 4.0, None),
            ]),
        ]
        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertEqual(result_data[self.work_type][0], 5)
        self.assertEqual(result_data[self.work_type][1], 40.0)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type_overtime][0], 1)
        self.assertEqual(result_data[self.work_type_overtime][1], 12.0)

        # reset and make two weeks
        # 38 hours in 1 week x 2
        input_work_data = [
            ((2020, 24, 1), [
                (self.work_type, 4.0, None),
                (self.work_type, 4.0, None),
            ]),
            ((2020, 24, 2), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
            ((2020, 24, 3), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
            ((2020, 24, 4), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
        ]
        work_data = []
        for data in input_work_data:
            work_data.append(data)
            work_data.append(((data[0][0], data[0][1]+1, data[0][2]), data[1]))

        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertTrue(self.work_type_overtime not in result_data)
        self.assertEqual(result_data[self.work_type][0], 8)
        self.assertEqual(result_data[self.work_type][1], 76.0)

        # 48 hours in 1 week, 38 hours in 1 week
        work_data += [
            ((2020, 24, 5), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
        ]
        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertEqual(result_data[self.work_type][0], 9)
        self.assertEqual(result_data[self.work_type][1], 78.0)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type_overtime][0], 0)
        self.assertEqual(result_data[self.work_type_overtime][1], 8.0)

        # 52 hours in 1 week, 38 hours in 1 week
        work_data += [
            ((2020, 24, 6), [
                (self.work_type, 4.0, None),
            ]),
        ]
        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertEqual(result_data[self.work_type][0], 9)
        self.assertEqual(result_data[self.work_type][1], 78.0)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type_overtime][0], 1)
        self.assertEqual(result_data[self.work_type_overtime][1], 12.0)

    def test_03_overtime_aggregation_week_start(self):
        self.employee.resource_calendar_id.day_week_start = '7'
        self.test_02_overtime_aggregation()

    def test_10_overtime_aggregation_daily(self):
        self.overtime_rules.hours_per_day = 8.0
        self.overtime_rules.multiplier_per_day = 1.5
        # 38 hours in 1 week
        work_data = [
            ((2020, 24, 1), [
                (self.work_type, 4.0, None),
                (self.work_type, 4.0, None),
            ]),
            ((2020, 24, 2), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
            ((2020, 24, 3), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
            ((2020, 24, 4), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
        ]
        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertEqual(result_data[self.work_type][0], 4)
        self.assertEqual(result_data[self.work_type][1], 32.0)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type_overtime][0], 0)
        self.assertEqual(result_data[self.work_type_overtime][1], 6.0)

        # 48 hours in 1 week
        work_data += [
            ((2020, 24, 5), [
                (self.work_type, 10.0, None),
            ]),
        ]
        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertEqual(result_data[self.work_type][0], 5)
        self.assertEqual(result_data[self.work_type][1], 40.0)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type_overtime][0], 0)
        self.assertEqual(result_data[self.work_type_overtime][1], 8.0)

        # 52 hours in 1 week
        work_data += [
            ((2020, 24, 6), [
                (self.work_type, 4.0, None),
            ]),
        ]
        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertEqual(result_data[self.work_type][0], 5)
        self.assertEqual(result_data[self.work_type][1], 40.0)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type_overtime][0], 1)
        self.assertEqual(result_data[self.work_type_overtime][1], 12.0)

        # reset and make two weeks
        # 38 hours in 1 week x 2
        input_work_data = [
            ((2020, 24, 1), [
                (self.work_type, 4.0, None),
                (self.work_type, 4.0, None),
            ]),
            ((2020, 24, 2), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
            ((2020, 24, 3), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
            ((2020, 24, 4), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
        ]
        work_data = []
        for data in input_work_data:
            work_data.append(data)
            work_data.append(((data[0][0], data[0][1]+1, data[0][2]), data[1]))

        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type][0], 8)
        self.assertEqual(result_data[self.work_type][1], 64.0)
        self.assertEqual(result_data[self.work_type_overtime][0], 0)
        self.assertEqual(result_data[self.work_type_overtime][1], 12.0)

        # 48 hours in 1 week, 38 hours in 1 week
        work_data += [
            ((2020, 24, 5), [
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
        ]
        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertEqual(result_data[self.work_type][0], 9)
        self.assertEqual(result_data[self.work_type][1], 70.0)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type_overtime][0], 0)
        self.assertEqual(result_data[self.work_type_overtime][1], 16.0)

        # 52 hours in 1 week, 38 hours in 1 week
        work_data += [
            ((2020, 24, 6), [
                (self.work_type, 4.0, None),
            ]),
        ]
        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertEqual(result_data[self.work_type][0], 9)
        self.assertEqual(result_data[self.work_type][1], 70.0)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type_overtime][0], 1)
        self.assertEqual(result_data[self.work_type_overtime][1], 20.0)

    def test_11_overtime_aggregation_daily_week_start(self):
        self.employee.resource_calendar_id.day_week_start = '7'
        self.test_10_overtime_aggregation_daily()

    def test_12_recursive_daily(self):
        # recursive will use a second overtime
        self.work_type_overtime2 = self.env['hr.work.entry.type'].create({
            'name': 'Test Overtime 2',
            'code': 'TEST_OT2'
        })
        self.overtime_rules2 = self.env['hr.work.entry.overtime.type'].create({
            'name': 'Test2',
            'hours_per_week': 999.0,
            'hours_per_day': 12.0,
            'multiplier': 2.0,
        })
        self.overtime_rules.hours_per_day = 8.0
        self.overtime_rules.multiplier_per_day = 1.5
        self.work_type_overtime.overtime_type_id = self.overtime_rules2
        self.work_type_overtime.overtime_work_type_id = self.work_type_overtime2

        work_data = [
            ((2020, 24, 1), [
                # regular day
                (self.work_type, 4.0, None),
                (self.work_type, 4.0, None),
            ]),
            ((2020, 24, 2), [
                # 2hr overtime
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
            ((2020, 24, 3), [
                # 4hr overtime
                (self.work_type, 6.0, None),
                (self.work_type, 6.0, None),
            ]),
            ((2020, 24, 4), [
                # 4hr overtime
                # 2hr overtime2
                (self.work_type, 6.0, None),
                (self.work_type, 8.0, None),
            ]),
        ]

        result_data = self.payslip.aggregate_overtime(work_data)
        self.assertTrue(self.work_type in result_data)
        self.assertEqual(result_data[self.work_type][0], 4)
        self.assertEqual(result_data[self.work_type][1], 32.0)
        self.assertTrue(self.work_type_overtime in result_data)
        self.assertEqual(result_data[self.work_type_overtime][0], 0)
        self.assertEqual(result_data[self.work_type_overtime][1], 10.0)
        self.assertTrue(self.work_type_overtime2 in result_data)
        self.assertEqual(result_data[self.work_type_overtime2][0], 0)
        self.assertEqual(result_data[self.work_type_overtime2][1], 2.0)

    def test_13_recursive_infinite_trivial(self):
        # recursive should will use a second overtime, but not this time!
        self.overtime_rules.hours_per_day = 8.0
        self.overtime_rules.multiplier_per_day = 1.5
        self.work_type.overtime_type_id = self.overtime_rules
        # overtime goes to itself
        self.work_type.overtime_work_type_id = self.work_type

        work_data = [
            ((2020, 24, 2), [
                # 2hr overtime
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
        ]

        with self.assertRaises(UserError):
            result_data = self.payslip.aggregate_overtime(work_data)

    def test_14_recursive_infinite_loop(self):
        # recursive will use a second overtime, but not this time!
        self.overtime_rules.hours_per_day = 8.0
        self.overtime_rules.multiplier_per_day = 1.5
        self.work_type_overtime.overtime_type_id = self.overtime_rules
        # overtime goes back to worktype
        self.work_type_overtime.overtime_work_type_id = self.work_type

        work_data = [
            ((2020, 24, 2), [
                # 2hr overtime
                (self.work_type, 4.0, None),
                (self.work_type, 6.0, None),
            ]),
        ]

        with self.assertRaises(UserError):
            result_data = self.payslip.aggregate_overtime(work_data)
