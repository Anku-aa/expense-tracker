#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime
import csv

# Define the path for the data file in the user's home directory
HOME_DIR = os.path.expanduser("~")
DATA_FILE = os.path.join(HOME_DIR, ".expenses.json")


def load_data():
    """Loads expense data from the JSON file."""
    if not os.path.exists(DATA_FILE):
        # Create a default structure if the file doesn't exist
        return {"expenses": [], "metadata": {"last_id": 0, "budgets": {}}}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # Handle cases where the file is empty or corrupted
        return {"expenses": [], "metadata": {"last_id": 0, "budgets": {}}}


def save_data(data):
    """Saves the given data to the JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def add_expense(args):
    """Adds a new expense."""
    data = load_data()

    # Generate new ID
    new_id = data["metadata"]["last_id"] + 1
    data["metadata"]["last_id"] = new_id

    expense = {
        "id": new_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": args.description,
        "amount": args.amount,
        "category": args.category.capitalize() if args.category else "General",
    }

    data["expenses"].append(expense)
    save_data(data)
    print(f"✅ Expense added successfully (ID: {new_id})")


def list_expenses(args):
    """Lists all expenses, with optional filtering by category."""
    data = load_data()
    expenses = data.get("expenses", [])

    if not expenses:
        print("No expenses recorded yet.")
        return

    # Filter by category if the argument is provided
    if args.category:
        expenses = [
            exp for exp in expenses if exp["category"].lower() == args.category.lower()
        ]
        if not expenses:
            print(f"No expenses found in category '{args.category}'.")
            return

    # Print table header
    print(f"{'ID':<4} {'Date':<12} {'Amount':<10} {'Category':<15} {'Description'}")
    print("-" * 60)

    # Print each expense
    for exp in sorted(expenses, key=lambda x: x["date"]):
        print(
            f"{exp['id']:<4} {exp['date']:<12} ${exp['amount']:<9.2f} {exp['category']:<15} {exp['description']}"
        )


def update_expense(args):
    """Updates an existing expense by its ID."""
    data = load_data()
    expenses = data.get("expenses", [])
    expense_found = False

    for exp in expenses:
        if exp["id"] == args.id:
            if args.description:
                exp["description"] = args.description
            if args.amount is not None:
                exp["amount"] = args.amount
            if args.category:
                exp["category"] = args.category.capitalize()
            expense_found = True
            break

    if expense_found:
        save_data(data)
        print(f"✅ Expense with ID {args.id} updated successfully.")
    else:
        print(f"❌ Error: Expense with ID {args.id} not found.")


def delete_expense(args):
    """Deletes an expense by its ID."""
    data = load_data()
    initial_count = len(data["expenses"])

    # Filter out the expense to be deleted
    data["expenses"] = [exp for exp in data["expenses"] if exp["id"] != args.id]

    if len(data["expenses"]) < initial_count:
        save_data(data)
        print(f"✅ Expense with ID {args.id} deleted successfully.")
    else:
        print(f"❌ Error: Expense with ID {args.id} not found.")


def show_summary(args):
    """Shows a summary of expenses."""
    data = load_data()
    expenses = data.get("expenses", [])

    if not expenses:
        print("No expenses to summarize.")
        return

    current_year = datetime.now().year

    # Filter by month if specified
    if args.month:
        try:
            month_num = int(args.month)
            if not 1 <= month_num <= 12:
                raise ValueError
            month_name = datetime(current_year, month_num, 1).strftime("%B")
            expenses = [
                exp
                for exp in expenses
                if datetime.strptime(exp["date"], "%Y-%m-%d").month == month_num
                and datetime.strptime(exp["date"], "%Y-%m-%d").year == current_year
            ]
            summary_title = f"Total expenses for {month_name} {current_year}"
        except ValueError:
            print("❌ Error: Invalid month. Please provide a number between 1 and 12.")
            return
    else:
        summary_title = "Total expenses"

    # Filter by category if specified
    if args.category:
        category = args.category.capitalize()
        expenses = [exp for exp in expenses if exp["category"] == category]
        summary_title += f" in category '{category}'"

    if not expenses:
        print("No expenses found for the specified criteria.")
        return

    total = sum(exp["amount"] for exp in expenses)
    print(f"📊 {summary_title}: ${total:.2f}")

    # Check against budget if a month is specified
    if args.month:
        budgets = data.get("metadata", {}).get("budgets", {})
        budget_for_month = budgets.get(str(args.month))
        if budget_for_month:
            print(f"   Budget for {month_name}: ${budget_for_month:.2f}")
            if total > budget_for_month:
                print(
                    f"   ⚠️ Warning: You have exceeded the budget by ${total - budget_for_month:.2f}."
                )
            else:
                print(f"   Remaining budget: ${budget_for_month - total:.2f}")


def set_budget(args):
    """Sets a monthly budget."""
    data = load_data()
    month_str = str(args.month)

    if "budgets" not in data["metadata"]:
        data["metadata"]["budgets"] = {}

    data["metadata"]["budgets"][month_str] = args.amount
    save_data(data)
    month_name = datetime(datetime.now().year, args.month, 1).strftime("%B")
    print(f"✅ Budget for {month_name} set to ${args.amount:.2f}.")


def export_to_csv(args):
    """Exports all expenses to a CSV file."""
    data = load_data()
    expenses = data.get("expenses", [])

    if not expenses:
        print("No expenses to export.")
        return

    filename = args.filename or "expenses.csv"

    try:
        with open(filename, "w", newline="") as csvfile:
            fieldnames = ["id", "date", "description", "amount", "category"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(expenses)
        print(f"✅ Expenses successfully exported to {filename}.")
    except IOError:
        print(f"❌ Error: Could not write to file {filename}.")


def main():
    """Main function to parse arguments and call appropriate handlers."""
    parser = argparse.ArgumentParser(
        description="A simple command-line expense tracker."
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new expense")
    add_parser.add_argument("amount", type=float, help="Amount of the expense")
    add_parser.add_argument(
        "-d",
        "--description",
        type=str,
        required=True,
        help="Description of the expense",
    )
    add_parser.add_argument(
        "-c",
        "--category",
        type=str,
        help="Category of the expense (e.g., Food, Transport)",
    )
    add_parser.set_defaults(func=add_expense)

    # List command
    list_parser = subparsers.add_parser("list", help="List all expenses")
    list_parser.add_argument(
        "-c", "--category", type=str, help="Filter expenses by category"
    )
    list_parser.set_defaults(func=list_expenses)

    # Update command
    update_parser = subparsers.add_parser("update", help="Update an existing expense")
    update_parser.add_argument("id", type=int, help="ID of the expense to update")
    update_parser.add_argument(
        "-a", "--amount", type=float, help="New amount for the expense"
    )
    update_parser.add_argument(
        "-d", "--description", type=str, help="New description for the expense"
    )
    update_parser.add_argument(
        "-c", "--category", type=str, help="New category for the expense"
    )
    update_parser.set_defaults(func=update_expense)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete an expense by ID")
    delete_parser.add_argument("id", type=int, help="ID of the expense to delete")
    delete_parser.set_defaults(func=delete_expense)

    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show a summary of expenses")
    summary_parser.add_argument(
        "-m",
        "--month",
        type=int,
        help="Summarize for a specific month (1-12) of the current year",
    )
    summary_parser.add_argument(
        "-c", "--category", type=str, help="Filter summary by category"
    )
    summary_parser.set_defaults(func=show_summary)

    # Budget command
    budget_parser = subparsers.add_parser("budget", help="Set a monthly budget")
    budget_parser.add_argument("amount", type=float, help="The budget amount")
    budget_parser.add_argument(
        "-m",
        "--month",
        type=int,
        required=True,
        help="Month (1-12) for which to set the budget",
    )
    budget_parser.set_defaults(func=set_budget)

    # Export command
    export_parser = subparsers.add_parser(
        "export", help="Export expenses to a CSV file"
    )
    export_parser.add_argument(
        "-f",
        "--filename",
        type=str,
        help="Optional name for the CSV file (default: expenses.csv)",
    )
    export_parser.set_defaults(func=export_to_csv)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
