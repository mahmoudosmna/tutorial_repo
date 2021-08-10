# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_round

STATUS = [
    ('draft', 'Employee/Worker'),
    ('department_manager', 'Department Manager'),
    ('hr_manager', 'HR Manager'),
    ('hr_manager', 'HR Manager'),
    ('done', 'Done'),
]


class Inherit_hr_leave_allocation(models.Model):
    _inherit = 'hr.leave.allocation'

    _sql_constraints = [
        ('type_value',
         "CHECK( (holiday_type='employee' AND employee_id IS NOT NULL) or "
         "(holiday_type='category' AND category_id IS NOT NULL) or "
         "(holiday_type='department' AND department_id IS NOT NULL) or "
         "(holiday_type='company' AND mode_company_id IS NOT NULL))",
         "The employee, department, company or employee category of this request is missing. Please make sure that your user login is linked to an employee."),
        ('duration_check', "CHECK ( number_of_days <= 0 )", "The number of days must be greater than 00."),
        ('number_per_interval_check', "CHECK(number_per_interval > 0)",
         "The number per interval should be greater than 0"),
        ('interval_number_check', "CHECK(interval_number > 0)", "The interval number should be greater than 0"),
    ]


###################################### Annual Leave ####################################################################
class annual_leave(models.Model):
    _name = 'annual.leave'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _rec_name = 'employee_id'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    def bntton_submit(self):
        for rec in self:
            if rec.remaining_leaves <= 0:
                raise ValidationError(_('The Remaining Leaves days Must be Greater Than 0..!'))
                # print("=====================", rec.remaining_leaves)
            else:
                rec.write({
                    'state': 'department_manager'
                })

    def bntton_dept_approve(self):
        self.acvtivity_id.unlink()
        for rec in self:
            group_department = self.env.ref('hr.group_hr_manager').id
            self.env.cr.execute(
                '''SELECT uid FROM res_groups_users_rel WHERE gid = %s order by uid''' % (
                    group_department))

            # schedule activity for user(s) to approve
            for fm in list(filter(lambda x: (
                    self.env['res.users'].sudo().search([('id', '=', x)])),
                                  self.env.cr.fetchall())):
                vals = {
                    'activity_type_id': self.env['mail.activity.type'].sudo().search(
                        [('name', 'like', u'Exception')],
                        limit=1).id,
                    'res_id': self.id,
                    'res_model_id': self.env['ir.model'].sudo().search(
                        [('model', 'like', 'annual.leave')], limit=1).id,
                    'user_id': fm[0] or 1,
                    'summary': u'New Employment Grievance ',
                }

                # add lines
                acvtivity_id = self.env['mail.activity'].sudo().create(vals)
            rec.state = 'hr_manager'

    def bntton_hr_approve(self):
        for rec in self:
            self.bntton_done()
            rec.state = 'done'


    def bntton_done(self):
        for rec in self:
            print("==============", type(int(rec.buy_days)))
            create_leave = self.env['hr.leave.allocation'].create({
                'name': 'Buy Leave',
                'employee_id': rec.employee_id.id,
                'holiday_status_id': rec.leave_type_id.id,
                'allocation_type': 'regular',
                'number_of_days': -int(rec.buy_days)
            })
            create_leave.action_approve()
            rec.state = 'done'

    ####################### Fields ########################################################################

    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  required=True)
    user_id = fields.Many2one(comodel_name="res.users", string="user", default=lambda self: self.env.user)
    dept_id = fields.Many2one(comodel_name="hr.department", string="Department", related='employee_id.department_id')
    buy_days = fields.Integer(string="Buy days", required=True, )
    rest = fields.Float(string="Rest", required=False, readonly=True, compute='_calc_leave')
    leave_type_id = fields.Many2one(comodel_name="hr.leave.type", string="Leave Type", required=True, )
    remaining_leaves = fields.Float(string="Remaining Leaves", required=False,
                                    related='employee_id.remaining_leaves')
    remaining_leaves_from_hr_leave = fields.Float(string="Remaining Leaves", required=False,
                                   compute='get_remaining_leaves',)
    enrollment_join = fields.Date(string="Enrollment Date",related='employee_id.enrollment_date')
    amount = fields.Float(string="Amount", required=False, )
    request_date = fields.Datetime(string="Request Date", readonly=True, default=fields.Datetime.now)
    state = fields.Selection(string="state", selection=STATUS, required=False, default='draft')
    acvtivity_id = fields.Many2one('mail.activity', string="Activity")

    @api.depends('buy_days', 'remaining_leaves')
    def _calc_leave(self):
        for rec in self:
            if int(rec.buy_days == 0):
                print("=============================")
            else:
                no = int(rec.buy_days)
                rec.rest = rec.remaining_leaves_from_hr_leave - no


    @api.depends('leave_type_id')
    def get_remaining_leaves(self):
        for rec in self:
            if rec.leave_type_id:
                rec.remaining_leaves_from_hr_leave = rec.leave_type_id.remaining_leaves
