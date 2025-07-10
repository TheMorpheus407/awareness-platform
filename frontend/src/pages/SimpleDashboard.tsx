import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api/client';

export default function SimpleDashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [userRes, statsRes, coursesRes] = await Promise.all([
        apiClient.get('/auth/me'),
        apiClient.get('/analytics/dashboard'),
        apiClient.get('/courses'),
      ]);
      
      setUser(userRes.data);
      setStats(statsRes.data);
      setCourses(coursesRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold">Awareness Platform</h1>
            <div className="flex items-center gap-4">
              <span>Welcome, {user?.email}</span>
              <button
                onClick={handleLogout}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold">Total Users</h3>
              <p className="text-3xl font-bold text-blue-600">{stats.total_users}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold">Courses Completed</h3>
              <p className="text-3xl font-bold text-green-600">{stats.courses_completed}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold">Compliance Rate</h3>
              <p className="text-3xl font-bold text-purple-600">{stats.compliance_rate}%</p>
            </div>
          </div>
        )}

        {/* Courses */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Available Courses</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {courses.map((course) => (
              <div key={course.id} className="border rounded p-4">
                <h3 className="font-semibold">{course.title}</h3>
                <p className="text-gray-600 text-sm">{course.description}</p>
                <button className="mt-2 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                  Start Course
                </button>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}