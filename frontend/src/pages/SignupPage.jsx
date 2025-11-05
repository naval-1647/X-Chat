import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function SignupPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', email: '', password: '', first_name: '', last_name: '', phone: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await register(form)
      navigate('/login')
    } catch (err) {
      let errorMessage = 'Registration failed'
      if (err.response?.data) {
        const data = err.response.data
        if (typeof data.detail === 'string') {
          errorMessage = data.detail
        } else if (data.detail && Array.isArray(data.detail)) {
          errorMessage = data.detail.map(e => e.msg || e.message || 'Validation error').join(', ')
        } else if (data.message) {
          errorMessage = data.message
        }
      }
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-full max-w-lg p-6 bg-white rounded shadow">
        <h2 className="text-2xl font-semibold mb-4">Sign up</h2>
        {error && <div className="mb-2 text-red-600">{error}</div>}
        <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-2">
          <input name="username" placeholder="Username" className="p-2 border rounded" value={form.username} onChange={handleChange} />
          <input name="email" placeholder="Email" className="p-2 border rounded" value={form.email} onChange={handleChange} />
          <input type="password" name="password" placeholder="Password" className="p-2 border rounded" value={form.password} onChange={handleChange} />
          <input name="first_name" placeholder="First name" className="p-2 border rounded" value={form.first_name} onChange={handleChange} />
          <input name="last_name" placeholder="Last name" className="p-2 border rounded" value={form.last_name} onChange={handleChange} />
          <input name="phone" placeholder="Phone" className="p-2 border rounded" value={form.phone} onChange={handleChange} />

          <button className="py-2 px-4 bg-green-600 text-white rounded mt-2" disabled={loading}>{loading ? 'Signing up...' : 'Sign up'}</button>
        </form>

        <p className="mt-4 text-sm">Already have an account? <Link to="/login" className="text-blue-600">Login</Link></p>
      </div>
    </div>
  )
}
