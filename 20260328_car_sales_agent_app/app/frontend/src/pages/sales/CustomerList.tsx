import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiSearch, FiUser, FiDollarSign, FiMapPin } from 'react-icons/fi'
import { LuCar } from 'react-icons/lu'
import { HiOutlineSparkles } from 'react-icons/hi2'
import { Card } from '../../components/common/Card'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { Badge } from '../../components/common/Badge'
import { customerAPI } from '../../api'
import type { Customer } from '../../types'

export function CustomerList() {
  const navigate = useNavigate()
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    loadCustomers()
  }, [])

  const loadCustomers = async (searchTerm?: string) => {
    setLoading(true)
    try {
      const data = await customerAPI.list({ search: searchTerm, limit: 50 })
      setCustomers(data)
    } catch (error) {
      console.error('Failed to load customers:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    loadCustomers(search)
  }

  const handleCustomerClick = (customerId: string) => {
    navigate(`/sales/customer/${customerId}`)
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
      maximumFractionDigits: 0,
    }).format(value)
  }

  // Get background gradient based on customer index for visual variety
  const getCustomerGradient = (index: number) => {
    const gradients = [
      'from-blue-50 to-indigo-50',
      'from-purple-50 to-pink-50',
      'from-emerald-50 to-teal-50',
      'from-amber-50 to-orange-50',
      'from-cyan-50 to-blue-50',
    ]
    return gradients[index % gradients.length]
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">顧客一覧</h1>
            <p className="text-sm text-gray-500 mt-1">
              顧客を選択してAI車両レコメンドを取得
            </p>
          </div>

          {/* Search */}
          <form onSubmit={handleSearch} className="flex items-center gap-2">
            <div className="relative">
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="顧客名・職業で検索..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 pr-4 py-2 w-64 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              検索
            </button>
          </form>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        ) : customers.length === 0 ? (
          <Card className="text-center py-12">
            <FiUser className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">顧客が見つかりませんでした</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {customers.map((customer, index) => (
              <Card
                key={customer.customer_id}
                className={`cursor-pointer hover:shadow-lg hover:border-blue-400 transition-all duration-200 bg-gradient-to-br ${getCustomerGradient(index)}`}
                onClick={() => handleCustomerClick(customer.customer_id)}
              >
                <div className="flex items-start gap-4">
                  {/* Avatar */}
                  <div className={`w-14 h-14 rounded-full flex items-center justify-center flex-shrink-0 ${
                    customer.gender === 'F' ? 'bg-pink-100' : 'bg-blue-100'
                  }`}>
                    <FiUser className={`w-7 h-7 ${
                      customer.gender === 'F' ? 'text-pink-600' : 'text-blue-600'
                    }`} />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-bold text-gray-900 truncate text-lg">
                        {customer.name}
                      </h3>
                      <Badge size="sm" variant="info">
                        {customer.age}歳
                      </Badge>
                    </div>

                    <p className="text-sm text-gray-600 font-medium">{customer.occupation}</p>

                    <p className="text-sm text-gray-500 mt-1 truncate">
                      {customer.family_structure}
                    </p>
                  </div>

                  {/* AI Icon */}
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-indigo-500 rounded-full flex items-center justify-center shadow-md">
                      <HiOutlineSparkles className="w-5 h-5 text-white" />
                    </div>
                  </div>
                </div>

                {/* Additional Info */}
                <div className="mt-4 pt-4 border-t border-gray-200/50 space-y-2">
                  {customer.location && (
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <FiMapPin className="w-4 h-4" />
                      <span>{customer.location}</span>
                    </div>
                  )}

                  {customer.current_car && (
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <LuCar className="w-4 h-4" />
                      <span className="truncate">{customer.current_car}</span>
                    </div>
                  )}

                  <div className="flex items-center gap-2 text-sm">
                    <FiDollarSign className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-700 font-medium">
                      {formatCurrency(customer.budget_min)} 〜 {formatCurrency(customer.budget_max)}
                    </span>
                  </div>
                </div>

                {/* View Recommendation Button */}
                <div className="mt-4 pt-4 border-t border-gray-200/50">
                  <button className="w-full flex items-center justify-center gap-2 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg hover:from-blue-600 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg">
                    <HiOutlineSparkles className="w-4 h-4" />
                    AI車両レコメンドを見る
                  </button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
