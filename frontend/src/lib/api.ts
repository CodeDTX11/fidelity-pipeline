import type { Transaction } from "../types/transaction";

export async function fetchTransactions(): Promise<Transaction[]> {
  const response = await fetch("/api/transactions", {
    headers: {
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json() as Promise<Transaction[]>;
}
