function ModelsProviders() {
  return (
    <div className="px-4 py-6 sm:px-0">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Models & Providers
      </h2>
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Active Model Profiles
        </h3>
        <p className="text-gray-600 mb-4">
          Configure model preferences, view token forecasts, and switch providers.
        </p>
        <div className="space-y-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-semibold text-gray-900">GPT-4 Turbo</h4>
                <p className="text-sm text-gray-500">OpenAI - Chat Model</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-700">Est. Tokens: 125K/day</p>
                <p className="text-xs text-gray-500">$2.50/day forecast</p>
              </div>
            </div>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-semibold text-gray-900">Claude 3 Opus</h4>
                <p className="text-sm text-gray-500">Anthropic - Chat Model</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-700">Est. Tokens: 80K/day</p>
                <p className="text-xs text-gray-500">$4.00/day forecast</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ModelsProviders;
