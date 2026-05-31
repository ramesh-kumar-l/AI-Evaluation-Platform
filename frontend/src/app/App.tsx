import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "@/app/Layout";
import { DashboardPage } from "@/pages/DashboardPage";
import { EvaluationsPage } from "@/pages/EvaluationsPage";
import { EvaluationDetailPage } from "@/pages/EvaluationDetailPage";
import { ComparePage } from "@/pages/ComparePage";
import { DatasetsPage } from "@/pages/DatasetsPage";
import { AuditPage } from "@/pages/AuditPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="evaluations" element={<EvaluationsPage />} />
          <Route path="evaluations/:id" element={<EvaluationDetailPage />} />
          <Route path="compare" element={<ComparePage />} />
          <Route path="datasets" element={<DatasetsPage />} />
          <Route path="audit" element={<AuditPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
