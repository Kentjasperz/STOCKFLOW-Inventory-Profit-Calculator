"""
STOCKFLOW: Inventory & Profit Calculator
Entry point for the desktop GUI application.
"""
from stockflow.gui.app import StockFlowApp


def main():
    app = StockFlowApp()
    app.mainloop()


if __name__ == "__main__":
    main()
