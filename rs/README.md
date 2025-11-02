# SubSafe Commander (Rust)

Control your Fleet of Safes from the command line! Claim your $SAFE token airdrop in style.

This is the Rust implementation of the SubSafe Commander, providing the same functionality as the Python version with improved performance and type safety.

## Features

- ✅ Claim $SAFE token airdrops on behalf of sub-safes
- ✅ Add owners to multiple sub-safes
- ✅ Set/clear Snapshot delegates for governance
- ✅ Multisend transaction batching
- ✅ Integration with Dune Analytics
- ✅ Safe transaction encoding

## Installation

### Prerequisites

- Rust 1.70+ (install from [rustup.rs](https://rustup.rs/))

### Build from Source

```bash
cd rs
cargo build --release
```

The binary will be available at `target/release/subsafe-commander`.

## Usage

### Environment Variables

Create a `.env` file in the project root:

```bash
NODE_URL=https://rpc.ankr.com/eth
PARENT_SAFE=0x...
PROPOSER_PK=0x...  # Private key of Parent Owner
DUNE_API_KEY=your_dune_api_key
```

### Commands

#### Claim Airdrop

```bash
./target/release/subsafe-commander \
  --command claim \
  --parent 0xYourParentSafe \
  --sub-safes 0xChild1,0xChild2,0xChild3
```

Or fetch children from Dune:

```bash
./target/release/subsafe-commander \
  --command claim \
  --parent 0xYourParentSafe \
  --index-from 0 \
  --num-safes 10
```

#### Add Owner

```bash
./target/release/subsafe-commander \
  --command add-owner \
  --parent 0xYourParentSafe \
  --sub-safes 0xChild1,0xChild2 \
  --new-owner 0xNewOwnerAddress \
  --threshold 1
```

#### Set Snapshot Delegate

```bash
./target/release/subsafe-commander \
  --command set-delegate \
  --parent 0xYourParentSafe \
  --sub-safes 0xChild1,0xChild2 \
  --delegate 0xDelegateAddress
```

If `--delegate` is not provided, it defaults to the parent safe.

#### Clear Snapshot Delegate

```bash
./target/release/subsafe-commander \
  --command clear-delegate \
  --parent 0xYourParentSafe \
  --sub-safes 0xChild1,0xChild2
```

## Development

### Run Tests

```bash
cargo test
```

### Run with Logging

```bash
RUST_LOG=info cargo run -- --command claim --parent 0x...
```

### Format Code

```bash
cargo fmt
```

### Lint

```bash
cargo clippy
```

## Architecture

The Rust implementation follows a modular architecture:

- `main.rs` - CLI entry point and command routing
- `environment.rs` - Environment configuration
- `safe.rs` - Safe operations and transaction encoding
- `multisend.rs` - Multisend transaction batching
- `airdrop/` - Airdrop-specific logic
  - `allocation.rs` - Fetching allocation data
  - `encode.rs` - Encoding claim transactions
  - `tx.rs` - Transaction building
- `snapshot/` - Snapshot delegation
  - `delegate_registry.rs` - Delegation ID handling
  - `tx.rs` - Delegate transaction building
- `add_owner.rs` - Add owner functionality
- `token_transfer.rs` - ERC20 and native token transfers
- `dune.rs` - Dune Analytics integration using [`duners`](https://crates.io/crates/duners) crate
- `utils.rs` - Utility functions

## Differences from Python Version

1. **Type Safety**: Rust's strong type system prevents many runtime errors
2. **Performance**: Faster execution, especially for large batches
3. **Memory Safety**: No garbage collector, deterministic memory usage
4. **Async/Await**: Built-in async support with Tokio
5. **Error Handling**: Explicit error handling with `Result` types

## Docker Support

### Build Docker Image

```bash
docker build -f rs/Dockerfile -t subsafe-commander:rust .
```

### Run with Docker

```bash
docker run --rm --env-file .env \
  subsafe-commander:rust \
  --command claim \
  --parent $PARENT_SAFE
```

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `cargo test`
2. Code is formatted: `cargo fmt`
3. No clippy warnings: `cargo clippy`

## License

Same as the parent project.

## Acknowledgments

This is a Rust port of the original Python implementation. The core logic and algorithms remain the same, with adaptations for Rust's type system and best practices.

