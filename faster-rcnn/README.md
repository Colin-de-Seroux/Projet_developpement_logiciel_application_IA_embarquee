# Faster RCNN

## **Version**
This project is based on the `fasterrcnn_resnet50_fpn` architecture from the PyTorch library.

## **How to Use**

### Fine-tuning the Model
To fine-tune the `fasterrcnn_resnet50_fpn` model:
1. Open the `faster_rcnn_fine_tunning.ipynb` notebook.
2. Follow the instructions to:
   - Load the pre-trained model.
   - Prepare the dataset.
   - Train and fine-tune the model.

### Testing the Model
To test the model on different hardware platforms:
1. Open the `test_fasterrcnn.ipynb` notebook.
2. Load the fine-tuned model or use the pre-trained version.
3. Run the evaluation on the test dataset.
4. The results will be saved as JSON files in the `predictions/` directory.

### Benchmarking
Benchmark the model's performance on various platforms:
1. Open `benchmarking.ipynb`
2. change the model name and excute the code .