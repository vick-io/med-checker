"use client";

import { Key, useState } from "react";

interface InteractionResponse {
  interactions: Array<{
    medication1: string;
    medication2: string;
    interaction: string;
    severity: string;
  }>;
}

interface Suggestion {
  name: string;
  medscape_id: string;
}

const fetchSuggestions = async (query: string): Promise<Suggestion[]> => {
  const response = await fetch(
    `http://localhost:8000/search-medications?query=${query}`
  );
  const data = await response.json();
  return data.suggestions || [];
};

const fetchInteractions = async (
  medication: Suggestion,
  current_medications: Suggestion[]
): Promise<InteractionResponse> => {
  const response = await fetch("http://localhost:8000/check-interactions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      medication: medication,
      current_medications: current_medications,
    }),
  });
  return response.json();
};

export default function Home() {
  const [inputValue, setInputValue] = useState<string>("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [selectedMedications, setSelectedMedications] = useState<Suggestion[]>(
    []
  );
  const [interactionResults, setInteractionResults] =
    useState<InteractionResponse | null>(null);

  const handleInputChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value;
    setInputValue(value);

    if (value.length > 0) {
      const fetchedSuggestions = await fetchSuggestions(value);
      setSuggestions(fetchedSuggestions);
    } else {
      setSuggestions([]);
    }
  };

  const handleSelectMedication = async (medication: Suggestion) => {
    if (
      !selectedMedications.find(
        (med) => med.medscape_id === medication.medscape_id
      )
    ) {
      const interactions = await fetchInteractions(
        medication,
        selectedMedications
      );
      setSelectedMedications([...selectedMedications, medication]);
      setInteractionResults(interactions);
    }
    setInputValue("");
    setSuggestions([]);
  };

  const handleRemoveMedication = (medication: Suggestion) => {
    const updatedMedications = selectedMedications.filter(
      (med) => med.medscape_id !== medication.medscape_id
    );
    setSelectedMedications(updatedMedications);

    // Update interactions after removing a medication
    if (updatedMedications.length > 0) {
      fetchInteractions(updatedMedications[0], updatedMedications.slice(1))
        .then(setInteractionResults)
        .catch(console.error);
    } else {
      setInteractionResults(null);
    }
  };

  const handleClearMedications = () => {
    setSelectedMedications([]);
    setInteractionResults(null);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-6 bg-gray-100">
      <header className="text-center my-8">
        <h1 className="text-6xl font-bold text-indigo-600">Mediract</h1>
        <p className="text-xl text-gray-700 mt-4">
          Search for medications and check for interactions
        </p>
      </header>
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-2xl">
        <form className="space-y-4 relative">
          <div className="flex flex-col">
            <label
              htmlFor="medication"
              className="text-gray-700 font-medium mb-2"
            >
              Enter a drug, OTC or herbal supplement:
            </label>
            <input
              type="text"
              value={inputValue}
              onChange={handleInputChange}
              placeholder="Enter medication"
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-900"
            />
            {suggestions.length > 0 && (
              <ul
                className="absolute z-10 bg-white border border-gray-300 rounded-lg mt-2 w-full text-gray-900 shadow-lg"
                style={{ top: "100%" }}
              >
                {suggestions.map((suggestion) => (
                  <li
                    key={suggestion.medscape_id}
                    onClick={() => handleSelectMedication(suggestion)}
                    className="px-4 py-2 cursor-pointer hover:bg-gray-200"
                  >
                    {suggestion.name}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </form>
        <div className="mt-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Selected Medications
          </h2>
          <ul className="space-y-2">
            {selectedMedications.map((medication) => (
              <li
                key={medication.medscape_id}
                className="flex justify-between items-center bg-gray-50 p-4 rounded-lg shadow-md text-gray-900"
              >
                {medication.name}
                <button
                  onClick={() => handleRemoveMedication(medication)}
                  className="text-red-500 hover:text-red-700"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
          {selectedMedications.length > 0 && (
            <button
              onClick={handleClearMedications}
              className="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg shadow-lg"
            >
              Clear All Medications
            </button>
          )}
          {interactionResults && interactionResults.interactions && (
            <div className="mt-8 bg-gray-50 p-6 rounded-lg shadow-inner text-gray-900">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Interaction Results
              </h2>
              {interactionResults.interactions.map(
                (
                  interaction: {
                    medication1: string;
                    medication2: string;
                    interaction: string;
                    severity: string;
                  },
                  index: Key | null | undefined
                ) => (
                  <div
                    key={index}
                    className="mb-4 p-4 bg-white rounded-lg shadow-sm"
                  >
                    <p className="text-lg font-bold">
                      <strong className="text-indigo-600">
                        {interaction.medication1}
                      </strong>{" "}
                      interacts with{" "}
                      <strong className="text-indigo-600">
                        {interaction.medication2}
                      </strong>
                    </p>
                    <p className="mt-2 text-gray-700">
                      {interaction.interaction}
                    </p>
                    <p className="mt-1 text-gray-700">
                      <strong>Severity:</strong> {interaction.severity}
                    </p>
                  </div>
                )
              )}
            </div>
          )}
        </div>
      </div>
      <footer className="mt-4 p-6 w-full max-w-2xl text-center">
        <p className="text-gray-600">
          Not all drugs interact, and not every interaction means you must stop
          taking one of your medications. Always consult your healthcare
          provider about how drug interactions should be managed before making
          any changes to your current prescription.
        </p>
      </footer>
    </main>
  );
}
