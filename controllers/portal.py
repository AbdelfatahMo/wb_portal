from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from odoo.http import request
from odoo import http


class WbCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        rtn = super(WbCustomerPortal,
                    self)._prepare_home_portal_values(counters)
        rtn['students_count'] = request.env['wb.student'].search_count([])
        return rtn

    @http.route(['/my/students', '/my/students/page/<int:page>'], type='http', website=True)
    def wb_my_students(self, page=1, sortby='id', search='', search_in='All', **kwargs):

        # Search bar
        searchbar_sortings = {
            'id': {'label': 'ID DESC', 'order': 'id desc'},
            'name': {'label': 'Name', 'order': 'name'},
            'school_id': {'label': 'School', 'order': 'school_id.name'}
        }
        default_sort = searchbar_sortings[sortby]['order']

        # Search
        search_list = {
            'all': {'label': 'All', 'input': 'all', 'domain': ['|','|',('name', 'ilike', search),('school_id.name', 'ilike', search),('fees', '=', search)]},
            'name': {'label': 'Name', 'input': 'name', 'domain': [('name', 'ilike', search)]},
            'school': {'label': 'School', 'input': 'school_id', 'domain': [('school_id.name', 'ilike', search)]}
        }
        search_domain = search_list[search_in]['domain']

        students_obj = request.env['wb.student']

        pager_details = pager(
            '/my/students', total=students_obj.search_count(domain=search_domain), url_args={'sortby': sortby, 'search': search, 'search_in': search_in}, page=page, step=10)

        students = students_obj.search(
            domain=search_domain, limit=10, order=default_sort, offset=pager_details['offset'])

        qcontext = {'students': students, 'sortby': sortby, 'page_name': 'students_list',
                    'searchbar_sortings': searchbar_sortings, 'pager': pager_details,'search_in':search_in,'searchbar_inputs':search_list }
        return request.render('wb_portal.wb_student_list_view_portal', qcontext)

    @http.route(['/my/students/<model("wb.student"):id>'], type='http', website=True)
    def wb_my_students_student_form(self, id, **kwargs):
        print('--------------------------', id)
        # student = request.env['wb.student'].search([('id' , '=',id)])
        student_ids = request.env['wb.student'].search([]).ids
        total = len(student_ids)
        current_index = student_ids.index(id.id)
        qcontext = {'student': id, 'page_name': 'student'}
        if current_index != 0 and student_ids[current_index - 1]:
            qcontext['prev_record'] = f"/my/students/{student_ids[current_index -1]}"
        if current_index < total - 1 and student_ids[current_index + 1]:
            qcontext['next_record'] = f"/my/students/{student_ids[current_index +1]}"
        return request.render('wb_portal.wb_student_form_view_portal', qcontext)
