use env_logger::Builder;
use log::LevelFilter;
use std::io::Write;

/// Initialize the logger with a specific level
pub fn init_with_level(level: LevelFilter) {
    Builder::new()
        .format(|buf, record| {
            writeln!(
                buf,
                "{} [{}] - {}",
                chrono::Local::now().format("%Y-%m-%d %H:%M:%S"),
                record.level(),
                record.args()
            )
        })
        .filter_level(level)
        .parse_default_env()
        .init();
}
