import { Building, Ticket, Users, Receipt } from 'lucide-react';

const stats = [
  { label: 'Buildings', value: '12', icon: Building, color: 'bg-blue-500' },
  { label: 'Active Tickets', value: '28', icon: Ticket, color: 'bg-orange-500' },
  { label: 'Residents', value: '156', icon: Users, color: 'bg-green-500' },
  { label: 'This Month', value: '₺45,200', icon: Receipt, color: 'bg-purple-500' },
];

const recentTickets = [
  { id: 1, title: 'Broken elevator in Block A', status: 'in_progress', priority: 'high' },
  { id: 2, title: 'Water leak in apartment 5B', status: 'new', priority: 'urgent' },
  { id: 3, title: 'Street light not working', status: 'resolved', priority: 'low' },
];

export function DashboardPage() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-gray-900">Dashboard</h2>
        <p className="text-gray-500 mt-1">Overview of your CRM system</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{label}</p>
                <p className="text-2xl font-semibold text-gray-900 mt-1">{value}</p>
              </div>
              <div className={`${color} p-3 rounded-lg`}>
                <Icon size={24} className="text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Tickets</h3>
        <div className="space-y-3">
          {recentTickets.map(({ id, title, status, priority }) => (
            <div
              key={id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <Ticket size={20} className="text-gray-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{title}</p>
                  <p className="text-sm text-gray-500">#{id}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${
                    priority === 'urgent'
                      ? 'bg-red-100 text-red-700'
                      : priority === 'high'
                      ? 'bg-orange-100 text-orange-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {priority}
                </span>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full ${
                    status === 'new'
                      ? 'bg-blue-100 text-blue-700'
                      : status === 'in_progress'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-green-100 text-green-700'
                  }`}
                >
                  {status.replace('_', ' ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
