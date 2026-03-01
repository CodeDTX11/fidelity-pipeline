export type Transaction = {
  eventId: string;
  eventTs: string;
  customerId: string;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  sourceFile: string | null;
};
