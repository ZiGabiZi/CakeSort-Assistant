def create_move(
    source_row: int,
    source_column: int,
    destination_row: int,
    destination_column: int,
    slice_type: int,
    count: int
) -> dict[str,int]:
    return {
        "source_row": source_row,
        "source_column": source_column,
        "destination_row": destination_row,
        "destination_column": destination_column,
        "slice_type": slice_type,
        "count": count
    }