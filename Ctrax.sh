for f in *.avi;
do
Ctrax --Input=$f --Interactive=False --AutoEstimateBackground=False --AutoEstimateShape=False --CSVFile=${f%.*}.csv
done