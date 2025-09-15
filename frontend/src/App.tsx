import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import PatientForm from './components/PatientForm';
import PatientList from './components/PatientList';
import ChatInterface from './components/ChatInterface';
import { documentsApi, patientsApi } from './services/api';
import { DocumentProcessingResult, Patient, PatientCreate, PatientUpdate } from './types';
import './index.css';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'upload' | 'list' | 'chat'>('upload');
  const [isUploading, setIsUploading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [extractedData, setExtractedData] = useState<DocumentProcessingResult | null>(null);
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const [uploadedDocuments, setUploadedDocuments] = useState<File[]>([]);

  const handleFileUpload = async (file: File) => {
    // Stage files only; defer processing until Complete Upload
    setUploadedDocuments(prev => [...prev, file]);
  };

  const handleUploadComplete = async () => {
    if (uploadedDocuments.length === 0) {
      setShowForm(true);
      return;
    }

    setIsUploading(true);
    try {
      const result = await documentsApi.uploadDocuments(uploadedDocuments);
      setExtractedData(result);
      setShowForm(true);
    } catch (error) {
      console.error('Error processing documents:', error);
      alert('Failed to process documents. Please try again.');
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
      setShowForm(false);
      setUploadedDocuments([]);
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
    setShowForm(true);
    setCurrentView('upload');
  };

  const handleCancel = () => {
    setExtractedData(null);
    setEditingPatient(null);
    setShowForm(false);
    setUploadedDocuments([]);
    setCurrentView('upload');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'upload':
        return (
          <div className="max-w-4xl mx-auto space-y-8">
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                Patient Document Management
              </h1>
              <p className="text-gray-600">
                Upload patient documents to extract and organize medical information
              </p>
            </div>
            
            <DocumentUpload 
              onFileUpload={handleFileUpload} 
              onUploadComplete={handleUploadComplete}
              isUploading={isUploading} 
            />
            
            {/* Processing Status */}
            {uploadedDocuments.length > 0 && !showForm && (
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-sm text-blue-800">
                    <strong>{uploadedDocuments.length} document{uploadedDocuments.length !== 1 ? 's' : ''} selected.</strong>
                    {isUploading ? ' Processing...' : ' Click "Complete Upload & Process Documents" to continue.'}
                  </p>
                </div>
              </div>
            )}
            
            {/* Patient Form - Always visible below upload area */}
            {(showForm || editingPatient) && (
              <div className="border-t pt-8">
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
                  title={editingPatient ? 'Edit Patient Information' : 'Patient Information'}
                />
                
                {extractedData && (
                  <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                    <p className="text-sm text-yellow-800">
                      <strong>Confidence Score:</strong> {(extractedData.confidence_score * 100).toFixed(1)}%
                    </p>
                    <p className="text-sm text-yellow-700 mt-2">
                      Information extracted from {uploadedDocuments.length} document{uploadedDocuments.length !== 1 ? 's' : ''}. Please review and correct before saving.
                    </p>
                  </div>
                )}
              </div>
            )}
            
            {/* Manual Entry Option */}
            {!showForm && !editingPatient && (
              <div className="text-center border-t pt-8">
                <p className="text-gray-600 mb-4">
                  Or enter patient information manually
                </p>
                <button
                  onClick={() => setShowForm(true)}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Enter Patient Information Manually
                </button>
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
                onClick={() => {
                  setCurrentView('upload');
                  if (currentView !== 'upload') {
                    setShowForm(false);
                    setExtractedData(null);
                    setEditingPatient(null);
                    setUploadedDocuments([]);
                  }
                }}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'upload'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Home
              </button>
              
              <button
                onClick={() => {
                  setCurrentView('list');
                  setShowForm(false);
                  setExtractedData(null);
                  setEditingPatient(null);
                  setUploadedDocuments([]);
                }}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'list'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Patients
              </button>
              
              <button
                onClick={() => {
                  setCurrentView('chat');
                  setShowForm(false);
                  setExtractedData(null);
                  setEditingPatient(null);
                  setUploadedDocuments([]);
                }}
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
