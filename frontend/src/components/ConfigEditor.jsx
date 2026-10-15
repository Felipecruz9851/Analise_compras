import React, { useState, useEffect } from 'react';
import { apiCall } from '../services/api';

export default function ConfigEditor() {
  const [config, setConfig] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const res = await apiCall('obter_parametros', {});
      if (!res.erro) {
        setConfig(res);
        setEditForm(JSON.parse(JSON.stringify(res))); // clone
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSave = async () => {
    try {
      const res = await apiCall('salvar_parametros', editForm);
      if (res.status === 'ok') {
        setConfig(editForm);
        setEditing(false);
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <div className="text-sm p-4">Carregando...</div>;
  if (!config) return <div className="text-sm p-4">Erro ao carregar configuração.</div>;

  const handleChangeFaixa = (faixa, campo, valor) => {
    setEditForm((prev) => ({
      ...prev,
      faixas_compra: {
        ...prev.faixas_compra,
        [faixa]: {
          ...prev.faixas_compra[faixa],
          [campo]: Number(valor),
        },
      },
    }));
  };

  const handleChangeGeral = (campo, valor) => {
    setEditForm((prev) => ({
      ...prev,
      [campo]: Number(valor),
    }));
  };

  const isEditing = editing;

  return (
    <div className="bg-surface-canvas rounded-xl p-3 border border-border mb-4 shadow-sm">
      <div className="flex items-center justify-between text-on-surface-variant mb-3">
        <span className="text-xs uppercase tracking-wider font-semibold">Parâmetros Ativos</span>
        {!isEditing ? (
          <button onClick={() => setEditing(true)} className="text-primary hover:text-primary-light p-1">
            <span className="material-symbols-outlined text-[16px]">edit</span>
          </button>
        ) : (
          <div className="flex gap-2">
            <button onClick={() => { setEditing(false); setEditForm(JSON.parse(JSON.stringify(config))); }} className="text-error p-1">
              <span className="material-symbols-outlined text-[16px]">close</span>
            </button>
            <button onClick={handleSave} className="text-primary hover:text-primary-light p-1">
              <span className="material-symbols-outlined text-[16px]">save</span>
            </button>
          </div>
        )}
      </div>

      <div className="space-y-3 text-sm">
        {/* Configurações Gerais */}
        <div className="grid grid-cols-2 gap-2 pb-2 border-b border-border">
          <div>
            <div className="text-xs text-on-surface-variant">Teto Compra</div>
            {isEditing ? (
              <input type="number" className="w-full bg-white border border-border rounded px-1 py-0.5 text-xs" value={editForm.teto_compra} onChange={(e) => handleChangeGeral('teto_compra', e.target.value)} />
            ) : (
              <div className="font-semibold text-on-surface">R$ {config.teto_compra}</div>
            )}
          </div>
          <div>
            <div className="text-xs text-on-surface-variant">Estoque Seg (dias)</div>
            {isEditing ? (
              <input type="number" className="w-full bg-white border border-border rounded px-1 py-0.5 text-xs" value={editForm.estoque_seguranca_dias} onChange={(e) => handleChangeGeral('estoque_seguranca_dias', e.target.value)} />
            ) : (
              <div className="font-semibold text-on-surface">{config.estoque_seguranca_dias}</div>
            )}
          </div>
        </div>

        {/* Faixas */}
        <div className="pt-1">
          <div className="text-xs uppercase tracking-wider font-semibold mb-2 text-on-surface-variant">Faixas (Dias / R. Max / Ciclo)</div>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-on-surface-variant border-b border-border">
                <th className="pb-1 font-medium">Cls</th>
                <th className="pb-1 font-medium text-center">Cob.</th>
                <th className="pb-1 font-medium text-center">R.Mx</th>
                <th className="pb-1 font-medium text-center">Cicl.</th>
              </tr>
            </thead>
            <tbody>
              {['A', 'B', 'C'].map((f) => (
                <tr key={f} className="border-b border-border/50 last:border-0">
                  <td className="py-1 font-semibold">{f}</td>
                  <td className="py-1 text-center">
                    {isEditing ? (
                      <input type="number" className="w-10 text-center bg-white border border-border rounded px-1 py-0.5" value={editForm.faixas_compra[f].dias_cobertura} onChange={(e) => handleChangeFaixa(f, 'dias_cobertura', e.target.value)} />
                    ) : (
                      config.faixas_compra[f].dias_cobertura
                    )}
                  </td>
                  <td className="py-1 text-center">
                    {isEditing ? (
                      <input type="number" className="w-10 text-center bg-white border border-border rounded px-1 py-0.5" value={editForm.faixas_compra[f].recebimentos_max} onChange={(e) => handleChangeFaixa(f, 'recebimentos_max', e.target.value)} />
                    ) : (
                      config.faixas_compra[f].recebimentos_max
                    )}
                  </td>
                  <td className="py-1 text-center">
                    {isEditing ? (
                      <input type="number" className="w-10 text-center bg-white border border-border rounded px-1 py-0.5" value={editForm.faixas_compra[f].ciclo_compra} onChange={(e) => handleChangeFaixa(f, 'ciclo_compra', e.target.value)} />
                    ) : (
                      config.faixas_compra[f].ciclo_compra
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
