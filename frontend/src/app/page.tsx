"use client";

import { Key, useState } from "react";

interface InteractionResponse {
  interactions: Array<{
    medication1: string;
    medication2: string;
    interaction: string;
  }>;
}

const fetchSuggestions = async (query: string): Promise<string[]> => {
  const response = await fetch(
    `http://localhost:8000/search-medications?query=${query}`
  );
  const data = await response.json();
  return data.suggestions || [];
};

const fetchInteractions = async (
  medication: string,
  current_medications: string[]
): Promise<InteractionResponse> => {
  const response = await fetch("http://localhost:8000/check-interactions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ medication, current_medications }),
  });
  return response.json();
};

export default function Home() {
  const [inputValue, setInputValue] = useState<string>("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedMedications, setSelectedMedications] = useState<string[]>([]);
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

  const handleSelectMedication = async (medication: string) => {
    const medName = medication.split(" (")[0]; // Extract medication name
    if (!selectedMedications.includes(medName)) {
      const interactions = await fetchInteractions(
        medName,
        selectedMedications
      );
      setSelectedMedications([...selectedMedications, medName]);
      setInteractionResults(interactions);
    }
    setInputValue("");
    setSuggestions([]);
  };

  const handleRemoveMedication = (medication: string) => {
    const updatedMedications = selectedMedications.filter(
      (med) => med !== medication
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
    <main className="flex min-h-screen flex-col items-center justify-start p-6 bg-gray-50">
      <header className="text-center my-8">
        <h1 className="text-6xl font-bold text-purple-700">Mediract</h1>
        <p className="text-xl text-gray-600 mt-4">
          Search for medications and check for interactions
        </p>
      </header>
      <div className="bg-purple-100 p-8 rounded-lg shadow-lg w-full max-w-2xl">
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
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-400 text-black"
            />
            {suggestions.length > 0 && (
              <ul
                className="absolute z-10 bg-white border border-gray-300 rounded-lg mt-2 w-full text-black"
                style={{ top: "100%" }}
              >
                {suggestions.map((suggestion) => (
                  <li
                    key={suggestion}
                    onClick={() => handleSelectMedication(suggestion)}
                    className="px-4 py-2 cursor-pointer hover:bg-gray-200"
                  >
                    {suggestion}
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
                key={medication}
                className="flex justify-between items-center bg-white p-4 rounded-lg shadow-md text-black"
              >
                {medication}
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
              className="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg"
            >
              Clear All Medications
            </button>
          )}
          {interactionResults && interactionResults.interactions && (
            <div className="mt-8 bg-white p-4 rounded-lg shadow-inner">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Interaction Results
              </h2>
              {interactionResults.interactions.map(
                (
                  interaction: {
                    medication1: string;
                    medication2: string;
                    interaction: string;
                  },
                  index: Key | null | undefined
                ) => (
                  <div key={index} className="mb-2">
                    <p>
                      <strong>{interaction.medication1}</strong> interacts with{" "}
                      <strong>{interaction.medication2}</strong>
                    </p>
                    <p>{interaction.interaction}</p>
                  </div>
                )
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
