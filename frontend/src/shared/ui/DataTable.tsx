import { flexRender, type Table } from "@tanstack/react-table";
import { ArrowUpDown } from "lucide-react";

type DataTableProps<TData> = {
  table: Table<TData>;
  emptyMessage: string;
};

export function DataTable<TData>({ table, emptyMessage }: DataTableProps<TData>) {
  return (
    <div className="table-wrap desktop-only">
      <table className="data-table" role="table">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                const canSort = header.column.getCanSort();

                return (
                  <th key={header.id}>
                    {canSort ? (
                      <button
                        className="table-sort"
                        type="button"
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        <ArrowUpDown size={14} />
                      </button>
                    ) : (
                      <span className="table-head-label">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                      </span>
                    )}
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>

        <tbody>
          {table.getRowModel().rows.length ? (
            table.getRowModel().rows.map((row) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td className="table-empty" colSpan={table.getVisibleLeafColumns().length}>
                {emptyMessage}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
