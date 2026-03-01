import { RefreshCw, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "./components/ui/alert";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Skeleton } from "./components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./components/ui/table";
import { fetchTransactions } from "./lib/api";
import type { Transaction } from "./types/transaction";

function formatTimestamp(timestamp: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(timestamp));
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD"
  }).format(value);
}

function App() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  async function loadTransactions() {
    setLoading(true);
    setError(null);

    try {
      const nextTransactions = await fetchTransactions();
      setTransactions(nextTransactions);
      setLastRefresh(new Date());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadTransactions();
  }, []);

  const statusLabel = loading ? "Refreshing" : error ? "Attention" : "Ready";

  return (
    <main className="min-h-screen px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <Card className="animate-fade-up overflow-hidden border-white/70 bg-white/70">
          <CardContent className="p-0">
            <div className="grid gap-6 p-6 md:grid-cols-[1.4fr_0.9fr] md:p-8">
              <div className="space-y-4">
                <div className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.2em] text-primary">
                  Fidelity Pipeline
                </div>
                <div className="space-y-3">
                  <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-foreground md:text-6xl">
                    Transaction operations dashboard
                  </h1>
                  <p className="max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
                    Review transaction records flowing through the consumer API in a single interface tuned for
                    fast status checks and data inspection.
                  </p>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-3 md:grid-cols-1">
                <Card className="border-primary/10 bg-gradient-to-br from-primary/10 via-white to-white shadow-none">
                  <CardContent className="p-5">
                    <p className="text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground">Status</p>
                    <p className="mt-3 text-2xl font-semibold">{statusLabel}</p>
                  </CardContent>
                </Card>
                <Card className="border-primary/10 bg-white shadow-none">
                  <CardContent className="p-5">
                    <p className="text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground">Rows Returned</p>
                    <p className="mt-3 text-2xl font-semibold">{transactions.length}</p>
                  </CardContent>
                </Card>
                <Card className="border-primary/10 bg-white shadow-none">
                  <CardContent className="p-5">
                    <p className="text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground">Last Refresh</p>
                    <p className="mt-3 text-sm font-semibold md:text-base">
                      {lastRefresh ? lastRefresh.toLocaleTimeString() : "Not yet loaded"}
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="animate-fade-up border-white/80 bg-card/95 [animation-delay:120ms]">
          <CardHeader className="flex flex-col gap-4 border-b border-border/70 pb-5 md:flex-row md:items-end md:justify-between">
            <div className="space-y-2">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-primary">API Surface</p>
              <CardTitle>/api/transactions</CardTitle>
              <CardDescription>
                Same-origin React client with a Vite development proxy to the Spring Boot consumer on port 8080.
              </CardDescription>
            </div>
            <Button onClick={() => void loadTransactions()} disabled={loading} className="gap-2 self-start md:self-auto">
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh data
            </Button>
          </CardHeader>
          <CardContent className="space-y-5 pt-6">
            {error ? (
              <Alert>
                <TriangleAlert className="mb-3 h-5 w-5" />
                <AlertTitle>Unable to load transactions</AlertTitle>
                <AlertDescription>
                  The frontend could not retrieve `/api/transactions`. {error}
                </AlertDescription>
              </Alert>
            ) : null}

            <div className="overflow-hidden rounded-[24px] border border-border/80 bg-white">
              <Table>
                <TableHeader className="bg-muted/45">
                  <TableRow>
                    <TableHead>Event Id</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Customer Id</TableHead>
                    <TableHead>Symbol</TableHead>
                    <TableHead>Side</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                    <TableHead className="text-right">Price</TableHead>
                    <TableHead>Source File</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    Array.from({ length: 6 }).map((_, index) => (
                      <TableRow key={index}>
                        {Array.from({ length: 8 }).map((__, cellIndex) => (
                          <TableCell key={cellIndex}>
                            <Skeleton className="h-5 w-full max-w-[140px]" />
                          </TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : transactions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="py-12 text-center text-sm text-muted-foreground">
                        No transactions returned by the API.
                      </TableCell>
                    </TableRow>
                  ) : (
                    transactions.map((transaction) => (
                      <TableRow key={`${transaction.eventId}-${transaction.eventTs}`}>
                        <TableCell className="font-medium">{transaction.eventId}</TableCell>
                        <TableCell>{formatTimestamp(transaction.eventTs)}</TableCell>
                        <TableCell>{transaction.customerId}</TableCell>
                        <TableCell>{transaction.symbol}</TableCell>
                        <TableCell>
                          <Badge variant={transaction.side === "BUY" ? "success" : "danger"}>
                            {transaction.side}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right font-medium">{transaction.quantity.toLocaleString()}</TableCell>
                        <TableCell className="text-right font-medium">{formatCurrency(transaction.price)}</TableCell>
                        <TableCell className="text-muted-foreground">
                          {transaction.sourceFile || "Not supplied"}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

export default App;
