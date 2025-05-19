import React, { useEffect, ComponentType, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import './App.css';

// Create placeholder components as TypeScript-friendly fallbacks
const PlaceholderComponent = ({ name }: { name: string }) => (
  <div className="flex items-center justify-center h-screen">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
      <p className="mt-2 text-gray-500">Loading {name} component...</p>
    </div>
  </div>
);

function App() {
  const [Dashboard, setDashboard] = useState<ComponentType>(() => () => <PlaceholderComponent name="Dashboard" />);
  const [FlowBuilder, setFlowBuilder] = useState<ComponentType>(() => () => <PlaceholderComponent name="Flow Builder" />);
  const [Documents, setDocuments] = useState<ComponentType>(() => () => <PlaceholderComponent name="Documents" />);
  const [Chatbots, setChatbots] = useState<ComponentType>(() => () => <PlaceholderComponent name="Chatbots" />);
  const [FlowDetail, setFlowDetail] = useState<ComponentType>(() => () => <PlaceholderComponent name="Flow Detail" />);
  
  useEffect(() => {
    const loadComponents = async () => {
      try {
        const dashboardModule = await import('./pages/Dashboard');
        const flowBuilderModule = await import('./pages/FlowBuilder');
        const documentsModule = await import('./pages/Documents');
        const chatbotsModule = await import('./pages/Chatbots');
        const flowDetailModule = await import('./pages/FlowDetail');

        setDashboard(() => dashboardModule.default);
        setFlowBuilder(() => flowBuilderModule.default);
        setDocuments(() => documentsModule.default);
        setChatbots(() => chatbotsModule.default);
        setFlowDetail(() => flowDetailModule.default);

      } catch (error) {
        console.error('Failed to load components:', error);
        // Optionally, set an error state here to display a global error message
      }
    };

    loadComponents();
  }, []);

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/flows" element={<FlowBuilder />} />
          <Route path="/flows/:id" element={<FlowDetail />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/chatbots" element={<Chatbots />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
