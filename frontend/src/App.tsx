import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import PatientForm from './components/PatientForm';
import PatientList from './components/PatientList';
import ChatInterface from './components/ChatInterface';
import { documentsApi, patientsApi } from './services/api';
import { DocumentProcessingResult, Patient, PatientCreate, PatientUpdate } from './types';
import './index.css';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'upload' | 'form' | 'list' | 'chat'>('upload');
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [extractedData, setExtractedData] = useState<DocumentProcessingResult | null>(null);
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    try {
      const result = await documentsApi.uploadDocument(file);
      setExtractedData(result);
      setCurrentView('form');
    } catch (error) {
      console.error('Error uploading document:', error);
      alert('Failed to process document. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handlePatientSubmit = async (patientData: PatientCreate | PatientUpdate) => {
    setIsSubmitting(true);
    try {
      if (editingPatient) {
        // Update existing patient
        await patientsApi.updatePatient(editingPatient.id, patientData as PatientUpdate);
        alert('Patient updated successfully!');
        setEditingPatient(null);
      } else {
        // Create new patient - ensure we have all required fields
        const createData: PatientCreate = {
          name: patientData.name || '',
          date_of_birth: patientData.date_of_birth || '',
          diagnosis: patientData.diagnosis || '',
          prescription: patientData.prescription || ''
        };
        await patientsApi.createPatient(createData);
        alert('Patient created successfully!');
      }
      
      setExtractedData(null);
      setCurrentView('list');
      setRefreshTrigger(prev => prev + 1);
    } catch (error) {
      console.error('Error saving patient:', error);
      alert('Failed to save patient. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePatientEdit = (patient: Patient) => {
    setEditingPatient(patient);
    setCurrentView('form');
  };

  const handleCancel = () => {
    setExtractedData(null);
    setEditingPatient(null);
    setCurrentView('upload');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'upload':
        return (
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                Patient Document Management
              </h1>
              <p className="text-gray-600">
                Upload patient documents to extract and organize medical information
              </p>
            </div>
            <DocumentUpload onFileUpload={handleFileUpload} isUploading={isUploading} />
          </div>
        );
      
      case 'form':
        return (
          <div className="max-w-4xl mx-auto">
            <PatientForm
              initialData={
                extractedData?.extracted_data || 
                (editingPatient ? {
                  name: editingPatient.name,
                  date_of_birth: editingPatient.date_of_birth,
                  diagnosis: editingPatient.diagnosis || '',
                  prescription: editingPatient.prescription || ''
                } : undefined)
              }
              onSubmit={handlePatientSubmit}
              onCancel={handleCancel}
              isSubmitting={isSubmitting}
              title={editingPatient ? 'Edit Patient' : 'Verify Patient Information'}
            />
            
            {extractedData && (
              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm text-yellow-800">
                  <strong>Confidence Score:</strong> {(extractedData.confidence_score * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-yellow-700 mt-2">
                  Please review and correct the extracted information before saving.
                </p>
              </div>
            )}
          </div>
        );
      
      case 'list':
        return (
          <div className="max-w-6xl mx-auto">
            <PatientList 
              onPatientSelect={handlePatientEdit}
              refreshTrigger={refreshTrigger}
            />
          </div>
        );
      
      case 'chat':
        return (
          <div className="max-w-4xl mx-auto">
            <ChatInterface className="h-[600px]" />
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Patient DB
              </h1>
            </div>
            
            <div className="flex space-x-4 items-center">
              <button
                onClick={() => setCurrentView('upload')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'upload'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Upload
              </button>
              
              <button
                onClick={() => setCurrentView('list')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'list'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Patients
              </button>
              
              <button
                onClick={() => setCurrentView('chat')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'chat'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Chat
              </button>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Main Content */}
      <main className="py-8 px-4">
        {renderCurrentView()}
      </main>
    </div>
  );
};

export default App;
