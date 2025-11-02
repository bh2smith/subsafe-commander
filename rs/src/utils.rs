use anyhow::{Result, bail};

/// Partitions array into chunks of size `part_size`
pub fn partition_array<T: Clone>(arr: &[T], part_size: usize) -> Result<Vec<Vec<T>>> {
    if part_size == 0 {
        bail!("Can't partition array into parts of size 0");
    }

    let mut result = Vec::new();
    let mut i = 0;

    while i < arr.len() {
        let end = std::cmp::min(i + part_size, arr.len());
        result.push(arr[i..end].to_vec());
        i = end;
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_partition_array() {
        let arr = vec![1, 2, 3, 4, 5, 6, 7, 8, 9];
        let result = partition_array(&arr, 3).unwrap();
        assert_eq!(result, vec![vec![1, 2, 3], vec![4, 5, 6], vec![7, 8, 9]]);
    }

    #[test]
    fn test_partition_array_uneven() {
        let arr = vec![1, 2, 3, 4, 5];
        let result = partition_array(&arr, 2).unwrap();
        assert_eq!(result, vec![vec![1, 2], vec![3, 4], vec![5]]);
    }

    #[test]
    fn test_partition_array_zero_size() {
        let arr = vec![1, 2, 3];
        let result = partition_array(&arr, 0);
        assert!(result.is_err());
    }

    #[test]
    fn test_partition_array_larger_than_array() {
        let arr = vec![1, 2, 3];
        let result = partition_array(&arr, 10).unwrap();
        assert_eq!(result, vec![vec![1, 2, 3]]);
    }
}
