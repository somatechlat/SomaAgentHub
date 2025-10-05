function Marketplace() {
  return (
    <div className="px-4 py-6 sm:px-0">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Capsule Marketplace
      </h2>
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Available Task Capsules
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-semibold text-gray-900">Code Reviewer</h4>
                <p className="text-sm text-gray-500 mt-1">Automated PR analysis with security checks</p>
              </div>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                ✓ Verified
              </span>
            </div>
            <div className="mt-3 flex items-center text-sm text-gray-500">
              <span>Est. 5K tokens/run</span>
              <span className="mx-2">•</span>
              <span>by SomaTech</span>
            </div>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-semibold text-gray-900">Documentation Generator</h4>
                <p className="text-sm text-gray-500 mt-1">Auto-generate docs from codebase</p>
              </div>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                ✓ Verified
              </span>
            </div>
            <div className="mt-3 flex items-center text-sm text-gray-500">
              <span>Est. 8K tokens/run</span>
              <span className="mx-2">•</span>
              <span>by SomaTech</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Marketplace;
