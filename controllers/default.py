# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

	
def index():
	message = T('Welcome to our library site!')
	return locals()
	


@auth.requires_login()
def catalog():
	permission = auth.has_membership('librarian') or auth.has_membership('admin')
	grid = SQLFORM.grid(db.book, deletable=permission, editable=permission, csv=False, create=permission, details=False, paginate=25, 
		links=[dict(header='Link',body=lambda row: A(T('Show'), _class='btn', _href=URL('show',args=row.id)))])
	return locals()



@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin'))
def add_copy():
	book_id=request.args(0, cast=int)
	db.copies.book_id.default=book_id
	db.copies.book_id.writable=False
	db.copies.copy_status.default='available'
	form = SQLFORM(db.copies).process()
	if form.accepted:
		session.flash = T('Copy has been added')
		redirect(URL('copies_chck', args=book_id))
	return locals()

@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin') or auth.has_membership('reader'))
def show_copy():
	copy = db.copies(request.args(0, cast=int))
	return locals()


@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin') or auth.has_membership('reader'))
def copies_chck():
	book_id=request.args(0, cast=int)
	permission = auth.has_membership('librarian') or auth.has_membership('admin')
	grid = SQLFORM.grid(db.copies.book_id==book_id, args=request.args[:1], deletable=permission, editable=permission, csv=False, create=False, details=False, paginate=25, 
		links=[dict(header=T('Copy'),body=lambda row: A(T('Show copy'), _class='btn', _href=URL('show_copy',args=row.id))),])
	return locals()



@auth.requires_login()
def show():
	if request.args(0) and db.book(request.args(0, cast=int)):
		post = db.book(request.args(0, cast=int))
	else:
		session.flash = T('Book not found in database')
		redirect(URL('catalog'))
	return locals()



@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin'))
def deletesomething():
	db(db.auth_membership.id==request.args(0)).delete()
	redirect(URL('show_reader', args=request.args(1)), client_side=True)



@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin'))
def show_reader():
	if request.args(0) and db.auth_user(request.args(0, cast=int)):
		user = db.auth_user(request.args(0, cast=int))
		form2=''
		if (auth.has_membership('admin', user.id) or auth.has_membership('librarian', user.id)) and not auth.has_membership('admin'):
			session.flash = T('Insufficient privileges')
			redirect(URL('readers'))
		else:
			if not auth.has_membership('reader', user.id):
				form=FORM(INPUT(_type='submit', _value=T('Activate user')))
				if form.process().accepted:
					session.flash = T('User has been activated')
					db.auth_membership.update_or_insert(user_id=user.id,group_id=auth.id_group('reader'))
					redirect(URL('show_reader', args=user.id), client_side=True)
			else:
				form=FORM(INPUT(_type='submit', _value=T('Deactivate user')))
				if form.process().accepted:
					session.flash = T('User has been deactivated')
					db(db.auth_membership.user_id==user.id).delete()
					redirect(URL('show_reader', args=user.id), client_side=True)
			if auth.has_membership('admin'):
				db.auth_membership.user_id.default=user.id
				form2=SQLFORM(db.auth_membership).process()
				rows = db(db.auth_membership.user_id==user.id).select()
			return locals()
	else:
		session.flash = T('No such user')
		redirect(URL('readers'))



@auth.requires_membership('admin')
def manage_genres():
	grid = SQLFORM.grid(db.genres, csv=False, editable=False, details=False)
	return locals()


@auth.requires_membership('admin')
def all_users():
	grid = SQLFORM.grid(db.auth_user, deletable=False, editable=False, create=False, details=False, csv=False, paginate=25, 
		links=[dict(header='Link',body=lambda row: A(T('Show'), _class='btn', _href=URL('show_reader',args=row.id)))])
	return locals()
	


@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin'))
def readers():
	group_id = auth.id_group('reader')
	all_users_in_group = db(db.auth_membership.group_id==group_id)._select(db.auth_membership.user_id)
	users = db.auth_user.id.belongs(all_users_in_group)
	grid = SQLFORM.grid(users, deletable=False, editable=False, create=False, details=False, csv=False, paginate=25, 
		links=[dict(header='Link',body=lambda row: A(T('Show'), _class='btn', _href=URL('show_reader',args=row.id)))])
	return locals()



@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin') or auth.has_membership('reader'))
def show_loan():
	if request.args(0) and db.loans(request.args(0, cast=int)):
		loan=db.loans(request.args(0, cast=int))
		copy=db.copies(loan.copy_id)
	else:
		session.flash = T('Loan not found')
		if auth.has_membership('reader'):
			redirect(URL('catalog'))
		else:
			redirect(URL('reservations'))
	return locals()

@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin'))
def loan():
	if request.args(0) and db.loans(request.args(0, cast=int)):
		loan=db.loans(request.args(0, cast=int))
		loan.update_record(loan_status='loaned')
		copy=db.copies(loan.copy_id)
		copy.update_record(copy_status='loaned')
	redirect(URL('show_loan', args=request.args(0)), client_side=True)



@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin'))
def end_loan():
	if request.args(0) and db.loans(request.args(0, cast=int)):
		loan=db.loans(request.args(0, cast=int))
		loan.update_record(loan_status='ended')
		loan.update_record(end_date=request.utcnow)
		copy=db.copies(loan.copy_id)
		copy.update_record(copy_status='available')
	redirect(URL('show_loan', args=request.args(0)), client_side=True)

@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin'))
def reservations():
	grid = SQLFORM.grid(db.loans.loan_status=='reserved', deletable=False, editable=False, create=False, details=False, csv=False,
		links=[dict(header='Link',body=lambda row: A(T('Show'), _class='btn', _href=URL('show_loan',args=row.id)))])
	return locals()


@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin') or auth.has_membership('reader'))
def reserve():
	copy = db.copies(request.args(0, cast=int))
	if copy:
		if copy.copy_status=='available':
			db.loans.copy_id.default=copy.id
			db.loans.loan_status.writable= db.loans.start_date.writable=False
			db.loans.loan_status.readable=db.loans.end_date.readable=False
			db.loans.start_date.readable=db.loans.user_id.readable=db.loans.copy_id.readable=True
			db.loans.loan_status.default='reserved'
			db.loans.start_date.default=request.utcnow
			form = SQLFORM(db.loans).process()
			if form.accepted:
				session.flash = T('Book has been reserved')
				copy.update_record(copy_status='reserved')
				redirect(URL('catalog'))
	else:
		session.flash=T('Copy not found')
		redirect(URL('catalog'))
	return locals()



@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin'))
def loan_history():
	if request.args(0, cast=int):
		user=db.auth_user(request.args(0, cast=int))
		grid = SQLFORM.grid(db.loans.user_id==user.id, args=request.args[:1], deletable=False, editable=False, create=False, details=False, csv=False,
			links=[dict(header='Link',body=lambda row: A(T('Show'), _class='btn', _href=URL('show_loan',args=row.id)))])
	else:
		redirect(URL('reservations'))
	return locals()

@auth.requires(auth.has_membership('librarian') or auth.has_membership('admin') or auth.has_membership('reader'))
def own_loan_history():
	user_id=auth.user_id
	grid = SQLFORM.grid(db.loans.user_id==user_id, deletable=False, editable=False, create=False, details=False, csv=False,
		links=[dict(header='Link',body=lambda row: A(T('Show'), _class='btn', _href=URL('show_loan',args=row.id)))])
	return locals()


############DO NOT TOUCH!############





def user():
	"""
	exposes:
	http://..../[app]/default/user/login
	http://..../[app]/default/user/logout
	http://..../[app]/default/user/register
	http://..../[app]/default/user/profile
	http://..../[app]/default/user/retrieve_password
	http://..../[app]/default/user/change_password
	http://..../[app]/default/user/manage_users (requires membership in
	use @auth.requires_login()
		@auth.requires_membership('group name')
		@auth.requires_permission('read','table name',record_id)
	to decorate functions that need access control
	"""
	return dict(form=auth())

@cache.action()
def download():
	"""
	allows downloading of uploaded files
	http://..../[app]/default/download/[filename]
	"""
	return response.download(request, db)


def call():
	"""
	exposes services. for example:
	http://..../[app]/default/call/jsonrpc
	decorate with @services.jsonrpc the functions to expose
	supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
	"""
	return service()


@auth.requires_signature()
def data():
	"""
	http://..../[app]/default/data/tables
	http://..../[app]/default/data/create/[table]
	http://..../[app]/default/data/read/[table]/[id]
	http://..../[app]/default/data/update/[table]/[id]
	http://..../[app]/default/data/delete/[table]/[id]
	http://..../[app]/default/data/select/[table]
	http://..../[app]/default/data/search/[table]
	but URLs must be signed, i.e. linked with
	  A('table',_href=URL('data/tables',user_signature=True))
	or with the signed load operator
	  LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
	"""
	return dict(form=crud())
