import React, { useState, useEffect } from 'react';
import { Patient } from '../types';
import { patientsApi } from '../services/api';

interface PatientListProps {
  onPatientSelect?: (patient: Patient) => void;
  refreshTrigger?: number;
}

const PatientList: React.FC<PatientListProps> = ({ onPatientSelect, refreshTrigger }) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPatients = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await patientsApi.getAllPatients();
      setPatients(data);
    } catch (err) {
      setError('Failed to load patients');
      console.error('Error loading patients:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatients();
  }, [refreshTrigger]);

  const handleDelete = async (patientId: string) => {
    if (!window.confirm('Are you sure you want to delete this patient record?')) {
      return;
    }

    try {
      await patientsApi.deletePatient(patientId);
      setPatients(prev => prev.filter(p => p.id !== patientId));
    } catch (err) {
      console.error('Error deleting patient:', err);
      alert('Failed to delete patient');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600 text-center p-4">
        <p>{error}</p>
        <button
          onClick={loadPatients}
          className="mt-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (patients.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500">
        <p>No patients found.</p>
        <p className="text-sm mt-2">Upload a document to get started!</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Patient Records</h2>
        <p className="text-sm text-gray-600">{patients.length} patient(s) found</p>
      </div>
      
      <div className="divide-y divide-gray-200">
        {patients.map((patient) => (
          <div
            key={patient.id}
            className="p-6 hover:bg-gray-50 transition-colors"
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900">{patient.name}</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Born: {new Date(patient.date_of_birth).toLocaleDateString()}
                </p>
                
                {patient.diagnosis && (
                  <div className="mt-2">
                    <p className="text-sm font-medium text-gray-700">Diagnosis:</p>
                    <p className="text-sm text-gray-600">{patient.diagnosis}</p>
                  </div>
                )}
                
                {patient.prescription && (
                  <div className="mt-2">
                    <p className="text-sm font-medium text-gray-700">Prescription:</p>
                    <p className="text-sm text-gray-600">{patient.prescription}</p>
                  </div>
                )}
                
                <p className="text-xs text-gray-500 mt-3">
                  Added: {new Date(patient.created_at).toLocaleString()}
                  {patient.updated_at && (
                    <span className="ml-2">
                      • Updated: {new Date(patient.updated_at).toLocaleString()}
                    </span>
                  )}
                </p>
              </div>
              
              <div className="flex space-x-2 ml-4">
                {onPatientSelect && (
                  <button
                    onClick={() => onPatientSelect(patient)}
                    className="px-3 py-1 text-sm bg-primary-100 text-primary-700 rounded hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    Edit
                  </button>
                )}
                <button
                  onClick={() => handleDelete(patient.id)}
                  className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PatientList;
