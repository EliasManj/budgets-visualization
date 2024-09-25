sudo rm /etc/systemd/system/budgets-visualization.service
sudo cp budgets-visualization.service /etc/systemd/system/budgets-visualization.service
sudo systemctl daemon-reload
sudo systemctl enable budgets-visualization
sudo systemctl start budgets-visualization.service
sudo systemctl status budgets-visualization.service
