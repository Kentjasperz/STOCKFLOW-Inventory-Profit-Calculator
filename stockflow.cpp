#include <iostream>
#include <vector>
#include <string>
#include <iomanip>
#include <fstream>
using namespace std;

struct Item {
    string name;
    int initial_qty;
    int current_qty;
    double price;
    double cost;
};

vector<Item> inventory;

string getStockLevel(int qty) {
    if (qty < 0) return "No Stock";
    if (qty < 10) return "Low Stock";
    return "In Stock";
}

void displayMenu() {
    cout << "\n===== STOCK FLOW INVENTORY =====\n";
    cout << "1. Add Item\n";
    cout << "2. View Inventory\n";
    cout << "3. Edit Item\n";
    cout << "4. Remove Item\n";
    cout << "5. Check Status\n";
    cout << "6. Total Profit\n";
    cout << "7. Exit\n";
    cout << "Enter choice: ";
}

void addItem() {
    Item item;
    cout << "\n--- Add New Item ---\n";
    cout << "Item Name: ";
    cin.ignore();
    getline(cin, item.name);
    cout << "Initial Quantity: ";
    cin >> item.initial_qty;
    cout << "Current Quantity: ";
    cin >> item.current_qty;
    cout << "Selling Price: ";
    cin >> item.price;
    cout << "Cost Price: ";
    cin >> item.cost;
    
    inventory.push_back(item);
    
    cout << "\n✓ Item Added Successfully!\n";
}

void viewInventory() {
    if (inventory.empty()) {
        cout << "\nInventory is empty!\n";
        return;
    }
    
    cout << "\n--- INVENTORY LIST ---\n";
    cout << left<< setw(15) << "Item" << setw(13) << "Initial Qty" << setw(13) << "Current Qty" << setw(12) << "Price" << setw(12) << "Stock" << "\n";
    cout << string(60, '-') << "\n";
    
    for (int i = 0; i < inventory.size(); i++) {
        cout  << "[" << i+1 << "]" << left << setw(15) << inventory[i].name << setw(13) << inventory[i].initial_qty << setw(13) << inventory[i].current_qty
             << "P" << setw(11) << fixed << setprecision(2) << inventory[i].price
             << getStockLevel(inventory[i].current_qty) << "\n";
    }
}

void editItem() {
    if (inventory.empty()) {
        cout << "\nNo items to edit!\n";
        return;
    }
    
    viewInventory();
    cout << "\nEnter item number to edit (1-" << inventory.size() << "): ";
    int idx;
    cin >> idx;
    
    if (idx < 1 || idx > inventory.size()) {
        cout << "Invalid selection!\n";
        return;
    }
    
    idx--;
    cout << "\nEditing: " << inventory[idx].name << "\n";
    cout << "New Current Quantity: ";
    cin >> inventory[idx].current_qty;
    cout << "New Selling Price: ";
    cin >> inventory[idx].price;
    
    cout << "✓ Item updated!\n";
}

void removeItem() {
    if (inventory.empty()) {
        cout << "\nNo items to remove!\n";
        return;
    }
    
    viewInventory();
    cout << "\nEnter item number to remove (1-" << inventory.size() << "): ";
    int idx;
    cin >> idx;
    
    if (idx < 1 || idx > inventory.size()) {
        cout << "Invalid selection!\n";
        return;
    }
    
    idx--;
    string name = inventory[idx].name;
    inventory.erase(inventory.begin() + idx);
    cout << "✓ Removed: " << name << "\n";
}

void checkStatus() {
    if (inventory.empty()) {
        cout << "\nNo items in inventory!\n";
        return;
    }
    
    cout << "\n--- STOCK STATUS ---\n";
    for (int i = 0; i < inventory.size(); i++) {
        cout << "[" << i+1 << "]" << inventory[i].name << ": " 
             << inventory[i].current_qty << " units - "
             << getStockLevel(inventory[i].current_qty) << "\n";
    }
}

void totalProfit() {
    if (inventory.empty()) {
        cout << "\nNo items to calculate!\n";
        return;
    }
    
    double total = 0;
    cout << "\n--- PROFIT BREAKDOWN ---\n";
    
    for (int i = 0; i < inventory.size(); i++) {
        int sold = inventory[i].initial_qty - inventory[i].current_qty;
        double margin = inventory[i].price - inventory[i].cost;
        double profit = margin * sold;
        total += profit;
        
        cout  << "[" << i+1 << "]" << inventory[i].name << ": P" << fixed << setprecision(2) 
             << profit << " (" << sold << " sold)\n";
    }
    
    cout << "\nTOTAL PROFIT: P" << total << "\n";
}

int main() {
    int choice;
    
    cout << "===================================\n";
    cout << "   STOCK FLOW INVENTORY SYSTEM    \n";
    cout << "===================================\n";
    
    do {
        displayMenu();
        cin >> choice;
        
        switch(choice) {
            case 1: addItem(); break;
            case 2: viewInventory(); break;
            case 3: editItem(); break;
            case 4: removeItem(); break;
            case 5: checkStatus(); break;
            case 6: totalProfit(); break;
            case 7: cout << "\nGoodbye!\n"; break;
            default: cout << "\nInvalid choice!\n";
        }
    } while (choice != 7);
    
    return 0;
}
