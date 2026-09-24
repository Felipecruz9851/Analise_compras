import React from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import MetricsCards from './components/MetricsCards';
import PurchaseTable from './components/PurchaseTable';

function App() {
  return (
    <div className="bg-surface-canvas text-on-surface font-body min-h-screen">
      <Sidebar />
      <div className="pl-72 flex flex-col min-h-screen">
        <Header />
        <main className="w-full pt-20 bg-surface-canvas flex-1">
          <div className="flex flex-col w-full">
            <div className="p-lg space-y-xl max-w-[1720px] mx-auto w-full">
              <MetricsCards />
              <div className="grid grid-cols-1 xl:grid-cols-12 gap-md items-start mt-8">
                 {/* Sidebar Familias placeholder */}
                 <div className="xl:col-span-3 bg-surface-card rounded-lg p-md shadow-card">
                    <h3 className="font-bold text-lg mb-4">Famílias de Compra</h3>
                    <p className="text-sm text-text-secondary">Selecione uma família para filtrar.</p>
                 </div>
                 {/* Table */}
                 <div className="xl:col-span-9 bg-surface-card rounded-lg shadow-card">
                    <PurchaseTable />
                 </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
