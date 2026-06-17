import request from './request.js'

export function listRentals(params) {
  return request.get('/rentals', { params })
}

export function createRental(data) {
  return request.post('/rentals', data)
}

export function getRental(id) {
  return request.get(`/rentals/${id}`)
}

export function returnRental(id, data) {
  return request.post(`/rentals/${id}/return`, data)
}

export function updateDepositStatus(id, status) {
  return request.put(`/rentals/${id}/deposit`, null, { params: { deposit_status: status } })
}

export function getExpiringReminders(days = 7) {
  return request.get('/rentals/reminders/expiring', { params: { days } })
}

export function getOverdueReminders() {
  return request.get('/rentals/reminders/overdue')
}