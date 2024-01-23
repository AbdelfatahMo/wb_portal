from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from odoo.http import request
from odoo import http, _
from odoo.tools import groupby as gb
from operator import itemgetter
import re
from datetime import datetime


class WbCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        rtn = super(WbCustomerPortal,
                    self)._prepare_home_portal_values(counters)
        rtn['students_count'] = request.env['school.student'].search_count([])
        return rtn

    ##
    @http.route(['/my/students', '/my/students/page/<int:page>'], type='http', website=True, auth="public")
    def wb_my_students(self, page=1, sortby='id', search='', groupby='none', search_in='all', **kwargs):
        if not groupby:
            groupby = 'none'
        # Search bar
        searchbar_sortings = {
            'id': {'label': 'ID DESC', 'order': 'id desc'},
            'name': {'label': 'Name', 'order': 'name'},
            'school': {'label': 'School', 'order': 'school_id'}
        }
        default_sort = searchbar_sortings[sortby]['order']

        # Search
        search_list = {
            'all': {'label': 'All', 'input': 'all', 'domain': ['|', '|', ('name', 'ilike', search), ('school_id.name', 'ilike', search), ('total_fees', '=', search)]},
            'name': {'label': 'Name', 'input': 'name', 'domain': [('name', 'ilike', search)]},
            'school': {'label': 'School', 'input': 'school_id', 'domain': [('school_id.name', 'ilike', search)]}
        }
        search_domain = search_list[search_in]['domain']

        # Groupby
        groupby_list = {
            'none': {'input': 'none', 'label': _('None'), 'order': 1},
            'country_id': {'input': 'country_id', 'label': _('Country'), 'order': 1},
            'school_id': {'input': 'school_id', 'label': _('School'), 'order': 1},
        }

        student_groupby = groupby_list.get(groupby, {})
        if groupby in ('school_id', 'country_id'):
            student_groupby = student_groupby.get('input')
        else:
            student_groupby = ''

        students_obj = request.env['school.student']

        pager_details = pager(
            '/my/students', total=students_obj.sudo().search_count(domain=search_domain), url_args={'sortby': sortby, 'search': search, 'groupby': groupby, 'search_in': search_in}, page=page, step=10)

        students = students_obj.sudo().search(
            domain=search_domain, limit=10, order=default_sort, offset=pager_details['offset'])

        if student_groupby:
            students_group_list = [{student_groupby: k, 'students': students_obj.concat(
                *g)} for k, g in gb(students, itemgetter(student_groupby))]
        else:
            students_group_list = [{"students": students}]
        print(f'------------------------------- {students_group_list}')
        print(students_group_list)
        qcontext = {'default_url': '/my/students',
                    'students_group_list': students_group_list, 'sortby': sortby, 'groupby': groupby, 'page_name': 'students_list',
                    'searchbar_sortings': searchbar_sortings, 'pager': pager_details, 'search_in': search_in, 'searchbar_inputs': search_list, 'searchbar_groupby': groupby_list}
        return request.render('wb_portal.wb_student_list_view_portal', qcontext)

    ##
    @http.route(['/my/students/student/<model("school.student"):id>'], type='http', website=True, auth="user")
    def wb_my_students_student_form(self, id, **kwargs):
        print('--------------------------', id)
        # student = request.env['school.student'].search([('id' , '=',id)])
        student_ids = request.env['school.student'].search([]).ids
        total = len(student_ids)
        current_index = student_ids.index(id.id)
        qcontext = {'student': id, 'page_name': 'student'}
        if current_index != 0 and student_ids[current_index - 1]:
            qcontext['prev_record'] = f"/my/students/student/{student_ids[current_index -1]}"
        if current_index < total - 1 and student_ids[current_index + 1]:
            qcontext['next_record'] = f"/my/students/student/{student_ids[current_index +1]}"
        return request.render('wb_portal.wb_student_form_view_portal', qcontext)

    def validate_email(self, email):
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email)

    def validate_mobile_number(self, number):
        """Return True if the number is a valid Egyptian mobile number."""
        regex = r'^01[0125][0-9]{8}$'
        return re.match(regex, number)

    ##
    @http.route(['/new/student'], type='http', methods=["POST", "GET"], website=True, auth="public")
    def wb_reqister_student_form(self, **kwargs):
        context = {}
        schools = request.env['school.profile'].sudo().search([])
        context['schools'] = schools
        countries = request.env['res.country'].sudo().search([])
        context['countries'] = countries
        error_list = []
        if request.httprequest.method == "POST":
            vals = {'name': kwargs['firstName']+' '+kwargs['lastName'],
                    'bdate': kwargs['date'],
                    'gender': kwargs['gender'],
                    'email': kwargs['email'],
                    'phone': kwargs['phone'],
                    'school_id': int(kwargs['school']),
                    'country_id': int(kwargs['country'])}
            if datetime.strptime(vals['bdate'], "%Y-%m-%d").year < 5:
                error_list.append("Student Age less than 5 years old!")
            elif vals['gender'] not in ('male', 'female'):
                error_list.append('Invalid Gender data!')
            elif not self.validate_email(vals['email']):
                error_list.append('Invalid Email address!')
            elif not self.validate_mobile_number(vals['phone']):
                error_list.append('Invalid Egyption phone number!')
            elif not request.env['school.profile'].search([('id', '=', vals['school_id'])])[0]:
                error_list.append('Invalid School!')
            elif not request.env['res.country'].search([('id', '=', vals['country_id'])])[0]:
                error_list.append('Invalid Country!')
            else:
                context['success'] = 'Success Registration'
                request.env['school.student'].create(vals)
            context['error_list'] = error_list
        else:
            print(" ------------------------ Get method")
        return request.render('wb_portal.wb_new_student_form_view_portal', qcontext=context)

    ##
    @http.route(['/my/students/student/print/<model("school.student"):id>'], type="http", auth="user", website=True)
    def wb_my_student_report_print(self, id, **kw):

        return self._show_report(id, "pdf", "wbcustom_header_foooter_pdf.school_student_profile_report_temp", download=True)
