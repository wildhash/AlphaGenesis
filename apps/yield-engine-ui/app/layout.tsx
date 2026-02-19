import type { Metadata } from "next";
import "./globals.css";
import "@rainbow-me/rainbowkit/styles.css";
import { Web3Provider } from "@/providers/Web3Provider";
import { Header } from "@/components/Header";

export const metadata: Metadata = {
  title: "AlphaGenesis Yield Engine | Self-Driving DeFi on BNB Chain",
  description: "Autonomous yield optimization protocol on BNB Chain. Non-custodial, on-chain only, with no admin keys. Integrate AsterDEX, stack composability, automate everything, protect users.",
  keywords: ["DeFi", "Yield", "BNB Chain", "Autonomous", "Non-custodial", "AsterDEX"],
  authors: [{ name: "AlphaGenesis Team" }],
  openGraph: {
    title: "AlphaGenesis Yield Engine",
    description: "Self-Driving Yield Engine on BNB Chain",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <Web3Provider>
          <Header />
          {children}
        </Web3Provider>
      </body>
    </html>
  );
}
