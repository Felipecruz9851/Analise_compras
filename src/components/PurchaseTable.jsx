import React, { useState } from 'react';

const mockData = [
  {
    id: 'EMB-0941',
    description: 'Tambor Metálico 200L Tampa Removível',
    family: 'Embalagens',
    supplier: 'Metalúrgica Sul S/A',
    stock: 120,
    consumption: 450,
    price: 249.00,
    suggestedQty: 500
  },
  {
    id: 'QUI-4012',
    description: 'Polímero Granulado Farma',
    family: 'Matéria-Prima Química',
    supplier: 'PetroChem Brasil',
    stock: 340,
    consumption: 800,
    price: 280.00,
    suggestedQty: 750,
    editedQty: 1000
  }
];

export default function PurchaseTable() {
  const [data, setData] = useState(mockData);

  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-bg-main text-text-secondary text-xs uppercase tracking-wider sticky top-0">
            <th className="py-2.5 px-3 w-10 text-center"><input type="checkbox" className="accent-primary" /></th>
            <th className="py-2.5 px-3 font-semibold">Código</th>
            <th className="py-2.5 px-3 font-semibold">Descrição do Material</th>
            <th className="py-2.5 px-3 font-semibold">Fornecedor</th>
            <th className="py-2.5 px-3 font-semibold text-right">Estoque</th>
            <th className="py-2.5 px-3 font-semibold text-right">Preço Unit.</th>
            <th className="py-2.5 px-3 font-semibold text-center bg-cell-highlight-bg text-cell-highlight-text">Decisão</th>
            <th className="py-2.5 px-3 font-semibold text-right">Valor Comprado</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border text-sm text-text-main">
          {data.map(item => {
            const finalQty = item.editedQty || item.suggestedQty;
            const isEdited = !!item.editedQty;
            return (
              <tr key={item.id} className={`hover:bg-row-alt transition-colors ${isEdited ? 'bg-cell-edited-bg/30' : ''}`}>
                <td className="py-2 px-3 text-center"><input type="checkbox" defaultChecked className="accent-primary" /></td>
                <td className={`py-2 px-3 font-bold ${isEdited ? 'text-cell-edited-text' : 'text-primary'}`}>{item.id}</td>
                <td className="py-2 px-3">
                  <div className="font-medium truncate max-w-[200px]">{item.description}</div>
                  <span className="text-[10px] text-text-secondary">Família: {item.family}</span>
                </td>
                <td className="py-2 px-3 truncate max-w-[130px]">{item.supplier}</td>
                <td className="py-2 px-3 text-right">{item.stock} un</td>
                <td className="py-2 px-3 text-right">R$ {item.price.toFixed(2)}</td>
                <td className="py-2 px-3 text-center">
                  <input 
                    type="number" 
                    defaultValue={finalQty} 
                    className={`w-20 h-7 text-center font-bold rounded border ${isEdited ? 'border-cell-edited-border text-cell-edited-text' : 'border-border'}`} 
                  />
                </td>
                <td className={`py-2 px-3 font-bold text-right ${isEdited ? 'text-cell-edited-text' : 'text-primary'}`}>
                  R$ {(finalQty * item.price).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
