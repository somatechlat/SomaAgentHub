function Overview() {
  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 p-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          SomaGent Admin Console
        </h2>
        <p className="text-lg text-gray-600 mb-6">
          Sprint-4: Experience & Ecosystem is live. Monitor platform health, manage models, and explore the marketplace.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold text-gray-700 mb-2">Health Status</h3>
            <p className="text-2xl font-bold text-green-600">🟢 All Systems Operational</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold text-gray-700 mb-2">Active Sessions</h3>
            <p className="text-2xl font-bold text-blue-600">42</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold text-gray-700 mb-2">Token Usage (24h)</h3>
            <p className="text-2xl font-bold text-purple-600">1.2M</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Overview;
