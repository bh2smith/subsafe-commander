import { promises as fs, createReadStream } from "fs";
import path from "path";

import { BigNumberish } from "@ethersproject/bignumber";
import GnosisSafe from "@gnosis.pm/safe-contracts/build/artifacts/contracts/GnosisSafe.sol/GnosisSafe.json";
import csv from "csv-parser";
import { Contract, utils } from "ethers";
import { task } from "hardhat/config";
import { HardhatRuntimeEnvironment } from "hardhat/types";

import { prompt } from "./ts/tui";
const CALL = 0;

interface NativeTransfer {
  receiver: string;
  amount: BigNumberish;
}

export function gnosisSafeAt(address: string): Contract {
  return new Contract(address, GnosisSafe.abi);
}

const parseCsvFile = async function (
  filePath: string,
): Promise<NativeTransfer[]> {
  return new Promise((resolve, reject) => {
    const results: NativeTransfer[] = [];
    createReadStream(filePath, { encoding: "utf-8" })
      .pipe(csv())
      .on("data", (data) => results.push(data))
      .on("end", () => resolve(results))
      .on("error", (error) => reject(error));
  });
};

const parseTransferFile = async function (
  filename: string,
): Promise<NativeTransfer[]> {
  const ext = path.extname(filename).toLowerCase();
  let results;
  if (ext === ".csv") {
    results = await parseCsvFile(filename);
    results = results.map(({ amount, receiver }) => ({
      amount,
      receiver,
    }));
  } else if (ext === ".json") {
    results = JSON.parse(await fs.readFile(filename, "utf8"));
  } else {
    throw new Error(`unsupported file type ${ext}`);
  }
  return results;
};

const partitionedTransfers = function (
  payments: NativeTransfer[],
  size: number,
): NativeTransfer[][] {
  const numBatches = Math.ceil(payments.length / size);
  console.log(
    `Splitting ${payments.length} transfers into ${numBatches} batches of size ${size}`,
  );
  const output = [];

  for (let i = 0; i < payments.length; i += size) {
    output[output.length] = payments.slice(i, i + size);
  }

  return output;
};

interface Args {
  fundAccount: string;
  transferFile: string;
  batchSize: number | null;
}

async function batchTransfer(
  { fundAccount, transferFile, batchSize }: Args,
  hre: HardhatRuntimeEnvironment,
) {
  // TODO - figure out network max
  batchSize = batchSize || 200;
  const transfers = await parseTransferFile(transferFile);
  console.log(`Found ${transfers.length} valid elements in transfer file`);
  const masterSafe = await gnosisSafeAt(fundAccount);

  console.log("Preparing transaction data...");
  const partition = partitionedTransfers(transfers, batchSize);
  const transactionLists = partition.map((transferBatch) => {
    return transferBatch.map((transfer) => {
      const weiAmount = utils.parseUnits(transfer.amount.toString(10), 18);
      return {
        operation: CALL,
        to: transfer.receiver,
        value: weiAmount,
        data: "0x",
      };
    });
  });
  const numBundles = transactionLists.length;
  const lastBatch = transfers.length - (numBundles - 1) * batchSize;
  console.log(
    `Prepared ${numBundles} bundles of size ${batchSize} (last having ${lastBatch})`,
  );

  if (await prompt(hre, "Do you want to send these transactions to the EVM?")) {
    for (const transactions of transactionLists) {
      const numTransfers = transactions.length;
      const firstReceiver = transactions[0].to;
      const lastReceiver = transactions[numTransfers - 1].to;
      console.log(
        `initiating ${numTransfers} transfers from account ${firstReceiver} to ${lastReceiver}`,
      );
      // const transaction = await buildBundledTransaction(transactions);
      // await signAndExecute(masterSafe, transaction);
    }
  }
}

const setupBatchTransferTask: () => void = () => {
  task(
    "batch-transfer",
    "Constructs and initiates multisend transactions from a Gnosis Safe",
  )
    .addParam("fundAccount", "Address Gnosis Safe with funds to transfer")
    .addParam("transferFile", "csv file containing transfer data")
    .addOptionalParam(
      "batchSize",
      "If set, script will attempt to make batches a large as specified, otherwise batches will be default for network",
    )
    .setAction(batchTransfer);
};

export { setupBatchTransferTask };
