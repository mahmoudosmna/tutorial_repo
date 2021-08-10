# -*- coding: utf-8 -*-
# from odoo import http


# class EmploymentGrievance(http.Controller):
#     @http.route('/employment_grievance/employment_grievance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/employment_grievance/employment_grievance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('employment_grievance.listing', {
#             'root': '/employment_grievance/employment_grievance',
#             'objects': http.request.env['employment_grievance.employment_grievance'].search([]),
#         })

#     @http.route('/employment_grievance/employment_grievance/objects/<model("employment_grievance.employment_grievance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('employment_grievance.object', {
#             'object': obj
#         })
